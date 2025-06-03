# Trigger redeploy on Railway
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import json
import os
from dotenv import load_dotenv
#from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
print(f"TOKEN: {repr(TOKEN)}") # Debug print

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def normalize_term(term):
    """Normalize term format to FA/SP + YY format"""
    term = term.strip().upper()
    if 'FALL' in term or term.startswith('F'):
        # Extract year, handle both YYYY and YY
        year_part = ''.join(filter(str.isdigit, term))
        if len(year_part) >= 2:
            return f"FA{year_part[-2:]}"
        
    elif 'SPRING' in term or term.startswith('S'):
        # Extract year, handle both YYYY and YY
        year_part = ''.join(filter(str.isdigit, term))
        if len(year_part) >= 2:
            return f"SP{year_part[-2:]}"

    return term

def create_chart(grades, name, course_name=None):
    labels = list(grades.keys())
    values = [grades[label] for label in labels]
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='skyblue')
    title = f"{name} Grade Distribution"
    if course_name:
        title = f"{name} - {course_name} Grade Distribution"
    plt.title(title)
    plt.xlabel("Grade")
    plt.ylabel("Number of Students")
    plt.tight_layout()
    plt.savefig("grade_chart.png")
    plt.close()

@bot.command()
async def grades(ctx, *, args: str):
    print(f"Received command: {args}")
    parts = args.strip().split()
    if len(parts) < 3:
        await ctx.send("Please provide a course number, professor's last name, and term (e.g., !grades 111 BOKLAN FA24)")
        return

    # Parse arguments
    course_nbr_input = parts[0]
    prof_last_name_input = parts[1].strip().upper()
    term_input_raw = parts[2].strip()
    
    # Normalize the input term
    term_lookup_key = normalize_term(term_input_raw)
    

    # Load the JSON data
    try:
        with open('grades.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading grades.json: {e}")
        await ctx.send("Error loading grade data. Please try again later.")
        return

    # Find matching course data
    matching_key = None
    for key in data:
        # Split from right to handle potential commas in professor names
        parts = key.rsplit(', ', 2) 
        if len(parts) == 3:
            prof, course, term = parts
        elif len(parts) == 2: # Handle cases where there's no comma in prof name
            prof, course_term = parts
            course, term = course_term.rsplit(', ', 1)
        else:
            continue # Skip this key if format is unexpected
            
        # Compare using the normalized input term
        if (course.strip() == course_nbr_input and 
            prof.split(',')[0].strip().upper() == prof_last_name_input and 
            term == term_lookup_key):
            matching_key = key
            break

    if not matching_key:
        # Provide feedback including the normalized term attempted
        await ctx.send(f"No data found for CSCI {course_nbr_input} with Professor {prof_last_name_input} in {term_input_raw} (looked for {term_lookup_key})")
        return

    course_data = data[matching_key]
    
    # Create and send the chart
    create_chart(course_data['grades'], course_data['name'], f"CSCI {course_data['course']}")
    file = discord.File("grade_chart.png")

    # Create response message
    grade_lines = [f"{grade}: {count}" for grade, count in course_data['grades'].items() if count > 0]
    grade_text = "\n".join(grade_lines)
    response = (
        f"**Professor {course_data['name']} - CSCI {course_data['course']} ({course_data['term']})**\n"
        f"Average GPA: {course_data['avg_gpa']:.2f}\n\n"
        f"Grade Breakdown:\n{grade_text}"
    )
    await ctx.send(response, file=file)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# keep_alive() # Keep the flask server running in a separate thread (was for replit)
bot.run(TOKEN)
