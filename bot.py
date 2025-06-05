import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import json
import os
from dotenv import load_dotenv
# Potentially keep this commented out if you don't need it for local testing anymore
#from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
print(f"TOKEN: {repr(TOKEN)}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def normalize_term(term):
    """Normalize term format to FA/SP + YY format"""
    term = term.strip().upper()
    if 'FALL' in term or term.startswith('F'):
        # Handle both YYYY and YY year formats
        year_part = ''.join(filter(str.isdigit, term))
        if len(year_part) >= 2:
            return f"FA{year_part[-2:]}"

    elif 'SPRING' in term or term.startswith('S'):
        # Handle both YYYY and YY year formats
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
    if len(parts) < 2:
        await ctx.send("Please provide at least a course number and professor\'s last name (e.g., !grades 111 BOKLAN)")
        return

    # Parse arguments
    course_nbr_input = parts[0].strip()
    prof_last_name_input = parts[1].strip().upper()

    # Store the raw term input if provided
    term_input_raw = None
    if len(parts) >= 3:
        term_input_raw = parts[2].strip().upper()

    # Load the JSON data
    try:
        with open('grades.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading grades.json: {e}")
        await ctx.send("Error loading grade data. Please try again later.")
        return

    # Find matching course data
    matching_entries = []
    available_terms = []  # Track available terms for error message

    for key in data:
        # Split from right to handle potential commas in professor names
        parts_key = key.rsplit(', ', 2)
        if len(parts_key) == 3:
            prof, course, term = parts_key
        elif len(parts_key) == 2:  # Handle cases where there\'s no comma in prof name
            prof, course_term = parts_key
            course, term = course_term.rsplit(', ', 1)
        else:
            continue  # Skip this key if format is unexpected

        # Check if this matches the course and professor
        if (course.strip() == course_nbr_input and
            prof.split(',')[0].strip().upper() == prof_last_name_input):
            matching_entries.append(data[key])
            available_terms.append(term.strip())

    if not matching_entries:
        await ctx.send(f"No data found for CSCI {course_nbr_input} with Professor {prof_last_name_input} in any term.")
        return

    # If term is not provided, find the most recent term and display it
    if len(parts) == 2:
        # Sort entries by term to find the most recent
        most_recent_entry = sorted(matching_entries, key=lambda x: x['term'])[-1]
        course_data = most_recent_entry

        await ctx.send(f"No term provided. Displaying data for Professor {course_data['name']}'s most recent semester for CSCI {course_data['course']}: {course_data['term']}")

        # Create and send the chart and response message
        create_chart(course_data['grades'], course_data['name'], f"CSCI {course_data['course']}")
        file = discord.File("grade_chart.png")

        grade_lines = [f"{grade}: {count}" for grade, count in course_data['grades'].items() if count > 0]
        response = f"**Grade Distribution for CSCI {course_data['course']} - {course_data['name']} ({course_data['term']})**\n" + "\n".join(grade_lines)

        await ctx.send(response, file=file)
        return

    # If term is provided, look for exact match
    if term_input_raw:
        for entry in matching_entries:
            if entry['term'].upper() == term_input_raw:
                course_data = entry

                # Create and send the chart and response message
                create_chart(course_data['grades'], course_data['name'], f"CSCI {course_data['course']}")
                file = discord.File("grade_chart.png")

                grade_lines = [f"{grade}: {count}" for grade, count in course_data['grades'].items() if count > 0]
                response = f"**Grade Distribution for CSCI {course_data['course']} - {course_data['name']} ({course_data['term']})**\n" + "\n".join(grade_lines)

                await ctx.send(response, file=file)
                return

        # If we get here, the term was not found
        available_terms_unique = sorted(set(available_terms))
        terms_list = ", ".join(available_terms_unique)

        await ctx.send(f"No data found for CSCI {course_nbr_input} with Professor {prof_last_name_input} for term {term_input_raw}.\n"
                      f"Available terms for this professor and course: {terms_list}")
        return

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# This was likely for Replit, keep commented out for Railway
# keep_alive()

bot.run(TOKEN)  