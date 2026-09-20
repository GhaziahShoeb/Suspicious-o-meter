SCAM_KEYWORDS = [
    # Upfront fee language
    "registration fee", "processing fee", "training fee", "equipment fee", "pay to apply",
    # Money-transfer language
    "wire transfer", "send gift cards", "purchase gift cards", "deposit and forward", "cryptocurrency payment",
    # Guaranteed-outcome language
    "guaranteed employment", "guaranteed income", "guaranteed placement",
    # Suspicious interview language
    "interview via whatsapp", "interview via telegram", "no interview needed",
]


def keyword_filter(text: str) -> dict:
    text_lower = text.lower()
    matched = [kw for kw in SCAM_KEYWORDS if kw in text_lower]

    return {
        "flagged": len(matched) > 0,
        "matched_keywords": matched
    }


if __name__ == "__main__":
    samples = [
        ("SCAM", """Dear Student of VIT BHOPAL
Congratulations once again on being shortlisted for the Job Bridge Program 2026, specially designed for VIT students and powered by Unlox Academy in collaboration with the Ministry of Electronics and Information Technology (MeitY) and NASSCOM.
This is the final opportunity to complete your enrollment for the August-September Batch. All shortlisted students are requested to complete the enrollment process before 11:00 AM tomorrow to confirm their seat."""),

        ("LEGIT", """We're Hiring: Product Analyst (Python / PySpark / Athena / SQL)
Are you passionate about turning data into actionable insights?
We're looking for a Product Analyst who's eager to dive into data, build scalable pipelines, and contribute to real business impact from day one.
What We're Looking For:
- Strong proficiency in Python, PySpark, Athena, and SQL
- Solid analytical and problem-solving skills
- Eagerness to learn and work cross-functionally with data, product, and business teams
- Engineering background is a plus
Role Highlights:
- Build and maintain data workflows & visualisations for business intelligence
- Collaborate with teams to identify & process data
- Work on AWS-based analytical tools and reporting
Location: Gurgaon (WFO)
Interested candidates need to fill this form with their details for shortlisting --> https://lnkd.in/gYR7ubmB
Drop your Resume at sakshimittal1@policybazaar.com/jatinkumar4@policybazaar.com"""),

        ("AMBIGUOUS", """Dear Candidate,
Greetings from Wyreflow Technologies!
We are hiring Customer Support Interns for both US Client Projects and Domestic Client Projects. Candidates can apply for either or both opportunities based on their preference.
Position: Customer Support Intern
Duration: 2 Months
Work Mode: Onsite
Location: Bhopal
Eligibility: Students from all academic backgrounds and branches can apply.
Internship Opportunities
1. US Client Projects -- Paid Internship
- Stipend: ₹8,000 per month
- Opportunity to work on live projects involving international clients.
- Exposure to professional customer engagement and communication.
2. Domestic Client Projects -- Unpaid Internship
- Unpaid Internship
- Training will be provided as part of the internship.
- Opportunity to gain practical exposure to customer support and client engagement.
Perks & Benefits
- Internship Completion Certificate
- Performance-Based Letter of Recommendation (LOR)
- Live Project Exposure
- Practical experience in customer support and client engagement
- Training and learning opportunities for Domestic Client Projects
- Professional workplace exposure
Interview Details
Date: 23rd August 2026 (Sunday)
Mode: Onsite
Location: Bhopal
Who Can Apply
- Students from all academic backgrounds and branches
- Freshers are welcome to apply
- Candidates with good communication and interpersonal skills
- Candidates with a positive attitude and willingness to learn
- Candidates comfortable working onsite in Bhopal
Interested candidates are requested to fill out the Google Form below to apply for the internship opportunity:
Google Form: https://forms.gle/exzrc58vrb8kPhdZ6
Candidates interested in both paid and unpaid internship opportunities are welcome to apply.
Regards,
HR Team
Wyreflow Technologies"""),

        ("LEGIT", """#hiring at Temple.
1. Data Science Intern (3-6 months)
Looking for: strong Python skills, background in Data Science/AI/Statistics/Biomedical Engineering, good understanding of women's cycle health, and the ability to read and implement scientific research papers.
2. Manufacturing Operations (Full-time)
Looking for: background in engineering/operations/supply chain, strong spreadsheet skills, attention to detail, clear communication, and a genuine interest in manufacturing and process execution.
Both roles are based on-site in Gurugram.
If either of these sounds like you (or someone you know), write to me at akshita@temple.com"""),

        ("SCAM", """We're delighted to inform you that you've been shortlisted for an exclusive Training & Internship Program organized by Innoknowvex in collaboration with IBM."""),

        ("LEGIT", """Looking to kick-start your career in IT? Here's your opportunity!
Open Positions:
- Manual Testing
- Application Support
Location: Thane
Who Can Apply?
- Fresher Graduates 2025/2026 Passouts (B.E./B.Tech/MCA only)
- Basic understanding of Software Testing or Application Support
- Good communication and problem-solving skills
- Passion to learn and grow in the IT industry
If you're eager to build your career with exciting learning opportunities and real-time project exposure, we'd love to hear from you!
Interested candidates, please send your updated resume or tag someone who is looking for an opportunity.
viraj.s@3i-infotech.com"""),

        ("AMBIGUOUS", """About the job
Job Title: Artificial Intelligence Intern | Entry Level | Fresher | AI, Generative AI, Python / Remote
Company: Medinex Workforce
Internship Details: Mode: Virtual / Remote Duration: Flexible Stipend: ₹14,500/month - ₹15,900/month
About the Opportunity: Medinex Workforce is actively hiring Artificial Intelligence Interns for freshers and entry-level candidates who are interested in AI fundamentals, generative AI tools, Python programming, automation workflows, prompt design, and intelligent system concepts.
Key Responsibilities:
- Support AI research, tool exploration, and structured learning assignments
- Assist in using generative AI tools for content, data, or workflow support tasks
- Help prepare prompts, test outputs, and document observations
Who Can Apply:
- Freshers, entry-level candidates, or students pursuing/completing degrees in Computer Science, AI/ML, Data Science, IT, Engineering, Mathematics, Statistics, or related fields
Required Skills:
- Basic understanding of AI, machine learning, or automation concepts
- Familiarity with Python basics or willingness to learn AI-supported workflows"""),

        ("SCAM", """Email & Chat Process Intern | Customer Support | Email Handling | Chat Support | Communication
Medinex Workforce is hiring Email & Chat Process Interns for a full-time remote internship opportunity. This role is suitable for candidates who want practical exposure to customer support, email communication, live chat handling, query resolution, documentation, and professional client interaction.
Position: Email & Chat Process Intern
Internship Details: Employment Type: Full-time Internship Workplace: Remote Location: India Duration: 1 to 3 Months Stipend: ₹15,300 per month Application Deadline: 31 August 2026
About Medinex Workforce: Medinex Workforce is a staffing and recruitment support company helping organizations connect with skilled and reliable talent across India."""),

        ("SCAM (text alone won't reveal this - confirmed via external report)", """Company Description: A Neumann & Associates, LLC is a trusted mergers and acquisitions advisory firm serving business owners across the East Coast from Massachusetts to Florida. Since its founding in 2003, the firm has maintained an A+ BBB rating for over 20 years, completed more than 5,000 business valuations, and closed over 500 transactions.
Role Description: The Senior Managing Director is a full-time, remote leadership role responsible for overseeing regional business development and transaction advisory activities.
Qualifications:
- Proven experience in mergers and acquisitions, investment banking, business brokerage, or related corporate finance advisory roles
- Strong business development skills
- Bachelor's degree in finance, business, economics, or a related field; advanced credentials (MBA, CPA, CFA, or relevant certifications) are beneficial"""),

        ("LEGIT", """We're Hiring: Software Engineering Interns (6 Months)
Jigar Gupta & I are looking for final-year undergraduate / dual-degree engineering students (preferably Computer Science or related disciplines) who are excited to build AI-powered products at the intersection of technology, finance, and distributed systems.
We're looking for candidates who:
- Are available for a 6-month full-time internship over the next year.
- Have strong CS fundamentals and enjoy solving challenging engineering problems.
- Have experience with Golang (Python is a plus).
- Want to work on AI, backend systems, cloud infrastructure, and financial technology.
Please apply at: https://lnkd.in/gKGCfQ_i"""),
    ]

    for i, (expected_label, text) in enumerate(samples, start=1):
        result = keyword_filter(text)
        print(f"Posting {i} — expected: {expected_label} — flagged: {result['flagged']} — matched: {result['matched_keywords']}")