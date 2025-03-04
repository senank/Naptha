job_grader = """
You are tasked with grading the applicant information provided in the <resume> XML tag for a {job_name} position at Naptha AI.
The job description will be provided in the <job_info> XML tag.
Grade the applicant on a scale of 1-100 based on the following criterea:
- technical_expertise:
- practical_experience: 
- job_alignment: 

*Job description*
<job_info>{job_info}</job_info>

*Applicant information*
<resume>{applicant}</resume>
"""