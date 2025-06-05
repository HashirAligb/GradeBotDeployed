How to Use GradeBot

GradeBot allows you to quickly look up grade distribution data for specific courses and professors.


The main command is !grades.


Command Usage:
!grades <course_number> <professor_last_name> [term]
Arguments:
<course_number>: The number of the course (e.g., 111, 212, 370).
<professor_last_name>: The last name of the professor (e.g., CHYN, STEINBERG, GOLDBERG).
[term]: (Optional) The specific academic term (semester) you want data for. Use the format FAYY for Fall (e.g., FA21, FA23) or SPYY for Spring (e.g., SP20, SP23).


Examples:
!grades 111 CHYN FA21 - Get grade data for CSCI 111 with Professor CHYN in Fall 2021.
!grades 212 STEINBERG SP23 - Get grade data for CSCI 212 with Professor STEINBERG in Spring 2023.
!grades 370 GOLDBERG - If no term is specified, the bot will automatically show the data for the most recent semester Professor GOLDBERG taught CSCI 370.


Helpful Responses:
If data is found for the specific course, professor, and term you provided, the bot will display the grade breakdown and average GPA, along with a chart.
If you provide a course and professor but no term, the bot will show the data for the most recent term and let you know.
If you provide a course, professor, and term, but no data is available for that specific term, the bot will inform you and list the terms for which data is available for that professor and course.
If no data is found for the course and professor combination at all, the bot will let you know.
