import random
import numpy as np
from jinja2 import Template
from sympy import symbols, Eq, solve

def solve_equation(a: int, b: int, c: int) -> str:
    """Solve quadratic equation ax² + bx + c = 0 and return roots as a string."""
    x = symbols('x')
    equation = Eq(a*x**2 + b*x + c, 0)
    roots = solve(equation, x)
    return ", ".join(str(round(float(root.evalf()), 2)) for root in sorted(roots, key=lambda x: float(x.evalf())))

TEMPLATES = [
    # GATE AE Templates (Existing)
    {
        "template": Template("Solve {{a}}x² + {{b}}x + {{c}} = 0 for x (round to 2 decimal places)."),
        "difficulty": "beginner",
        "topic": "algebra",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "a": np.random.randint(1, 6),
            "b": np.random.randint(-5, 6),
            "c": np.random.randint(-5, 6)
        },
        "compute_answer": lambda params: solve_equation(params["a"], params["b"], params["c"]),
        "options": []
    },
    {
        "template": Template("The thrust of a jet engine with mass flow rate {{m}} kg/s and exhaust velocity {{v}} m/s is (in kN, to two decimal places):"),
        "difficulty": "beginner",
        "topic": "propulsion",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "m": np.random.randint(40, 60),
            "v": np.random.randint(300, 700)
        },
        "compute_answer": lambda params: f"{(params['m'] * params['v'] / 1000):.2f}",
        "options": []
    },
    {
        "template": Template("The lift coefficient of a wing at {{angle}}° angle of attack is (to two decimal places):"),
        "difficulty": "intermediate",
        "topic": "Aerodynamics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "angle": np.random.randint(2, 8)
        },
        "compute_answer": lambda params: f"B. {(2 * np.pi * params['angle'] * np.pi / 180):.2f}",
        "options": lambda params: [
            f"A. {(2 * np.pi * (params['angle'] + 1) * np.pi / 180):.2f}",
            f"B. {(2 * np.pi * params['angle'] * np.pi / 180):.2f}",
            f"C. {(2 * np.pi * max(1, params['angle'] - 1) * np.pi / 180):.2f}",
            f"D. {(2 * np.pi * (params['angle'] + 2) * np.pi / 180):.2f}"
        ]
    },
    {
        "template": Template("A simply supported beam (length {{L}} m, point load {{P}} kN at center) has maximum bending moment in kNm:"),
        "difficulty": "beginner",
        "topic": "Structures",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "L": np.random.randint(1, 4),
            "P": np.random.randint(5, 15)
        },
        "compute_answer": lambda params: f"{(params['P'] * params['L'] / 4):.2f}",
        "options": []
    },
    {
        "template": Template("A compressor stage has a stagnation pressure ratio of {{pr}}. If inlet stagnation temperature is {{T}} K, the outlet stagnation temperature is (in K, γ = 1.4, to two decimal places):"),
        "difficulty": "intermediate",
        "topic": "Propulsion",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "pr": round(np.random.uniform(1.1, 1.3), 1),
            "T": np.random.randint(280, 320)
        },
        "compute_answer": lambda params: f"{(params['T'] * (params['pr'] ** ((1.4 - 1) / 1.4))):.2f}",
        "options": []
    },
    {
        "template": Template("For an aircraft in a steady, level, coordinated turn at a turn radius of {{R}} m and velocity {{V}} m/s, the load factor is (to two decimal places):"),
        "difficulty": "advanced",
        "topic": "Flight Mechanics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "R": np.random.randint(500, 1500),
            "V": np.random.randint(50, 100)
        },
        "compute_answer": lambda params: f"B. {(np.sqrt(1 + (params['V']**2 / (9.81 * params['R']))**2)):.2f}",
        "options": lambda params: [
            f"A. {(np.sqrt(1 + (params['V']**2 / (9.81 * params['R']))**2) - 0.2):.2f}",
            f"B. {(np.sqrt(1 + (params['V']**2 / (9.81 * params['R']))**2)):.2f}",
            f"C. {(np.sqrt(1 + (params['V']**2 / (9.81 * params['R']))**2) + 0.2):.2f}",
            f"D. {(np.sqrt(1 + (params['V']**2 / (9.81 * params['R']))**2) + 0.4):.2f}"
        ]
    },
    {
        "template": Template("The sum of the eigenvalues of the matrix [[{{a}}, 0], [0, {{b}}]] is (to one decimal place):"),
        "difficulty": "advanced",
        "topic": "Engineering Mathematics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "a": np.random.randint(1, 5),
            "b": np.random.randint(1, 5)
        },
        "compute_answer": lambda params: f"{(params['a'] + params['b']):.1f}",
        "options": []
    },
    # GATE AE New Templates
    {
        "template": Template("A solid circular shaft of diameter {{d}} mm is subjected to a torque of {{T}} Nm. The maximum shear stress is (in MPa, to two decimal places):"),
        "difficulty": "intermediate",
        "topic": "Mechanics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "d": np.random.randint(20, 50),
            "T": np.random.randint(100, 500)
        },
        "compute_answer": lambda params: f"{((16 * params['T'] * 1000) / (np.pi * (params['d'] / 1000)**3) / 1e6):.2f}",
        "options": []
    },
    {
        "template": Template("The orbital velocity of a satellite in a circular orbit at {{h}} km altitude is (in km/s, to two decimal places, R = 6371 km, μ = 398600 km³/s²):"),
        "difficulty": "intermediate",
        "topic": "Space Dynamics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "h": np.random.randint(300, 600)
        },
        "compute_answer": lambda params: f"B. {(np.sqrt(398600 / (6371 + params['h']))):.2f}",
        "options": lambda params: [
            f"A. {(np.sqrt(398600 / (6371 + params['h'])) - 0.2):.2f}",
            f"B. {(np.sqrt(398600 / (6371 + params['h']))):.2f}",
            f"C. {(np.sqrt(398600 / (6371 + params['h'])) + 0.2):.2f}",
            f"D. {(np.sqrt(398600 / (6371 + params['h'])) + 0.4):.2f}"
        ]
    },
    {
        "template": Template("The determinant of the matrix [[{{a}}, {{b}}], [{{c}}, {{d}}]] is:"),
        "difficulty": "advanced",
        "topic": "Linear Algebra",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "a": np.random.randint(1, 5),
            "b": np.random.randint(1, 5),
            "c": np.random.randint(1, 5),
            "d": np.random.randint(1, 5)
        },
        "compute_answer": lambda params: f"{(params['a'] * params['d'] - params['b'] * params['c']):.0f}",
        "options": []
    },
    {
        "template": Template("For an ideal gas with specific heat at constant pressure {{cp}} J/kg·K and specific heat ratio {{gamma}}, the specific heat at constant volume is (in J/kg·K, to one decimal place):"),
        "difficulty": "beginner",
        "topic": "Thermodynamics",
        "goal": "GATE AE",
        "generate_params": lambda: {
            "cp": np.random.randint(1000, 1200),
            "gamma": round(np.random.uniform(1.3, 1.5), 2)
        },
        "compute_answer": lambda params: f"B. {(params['cp'] / params['gamma']):.1f}",
        "options": lambda params: [
            f"A. {(params['cp'] / params['gamma'] - 50):.1f}",
            f"B. {(params['cp'] / params['gamma']):.1f}",
            f"C. {(params['cp'] / params['gamma'] + 50):.1f}",
            f"D. {(params['cp'] / params['gamma'] + 100):.1f}"
        ]
    },
    # Amazon SDE Templates (Existing)
    {
        "template": Template("What is the time complexity of {{operation}} in a balanced binary search tree?"),
        "difficulty": "intermediate",
        "topic": "Data Structures",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "operation": random.choice(["searching", "insertion", "deletion"])
        },
        "compute_answer": lambda params: "B. O(log n)",
        "options": [
            "A. O(1)",
            "B. O(log n)",
            "C. O(n)",
            "D. O(n log n)"
        ]
    },
    {
        "template": Template("What is the space complexity of an adjacency {{structure}} representation of a graph with V vertices and E edges?"),
        "difficulty": "advanced",
        "topic": "Data Structures",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "structure": random.choice(["list", "matrix"])
        },
        "compute_answer": lambda params: "B. O(V + E)" if params["structure"] == "list" else "C. O(V²)",
        "options": [
            "A. O(V)",
            "B. O(V + E)",
            "C. O(V²)",
            "D. O(E²)"
        ]
    },
    {
        "template": Template("What is the maximum number of nodes in a binary tree of height {{h}}?"),
        "difficulty": "intermediate",
        "topic": "Data Structures",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "h": np.random.randint(2, 6)
        },
        "compute_answer": lambda params: f"{(2**params['h'] - 1):.0f}",
        "options": []
    },
    {
        "template": Template("Which AWS service provides a {{service_type}}?"),
        "difficulty": "beginner",
        "topic": "AWS",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "service_type": random.choice(["NoSQL database", "managed message queuing service"])
        },
        "compute_answer": lambda params: "B. DynamoDB" if params["service_type"] == "NoSQL database" else "A. SQS",
        "options": lambda params: [
            "A. SQS",
            "B. DynamoDB",
            "C. RDS",
            "D. Lambda"
        ] if params["service_type"] == "NoSQL database" else [
            "A. SQS",
            "B. SNS",
            "C. Kinesis",
            "D. Lambda"
        ]
    },
    # Amazon SDE New Templates
    {
        "template": Template("What is the time complexity of {{algorithm}} sort in the average case?"),
        "difficulty": "intermediate",
        "topic": "Algorithms",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "algorithm": random.choice(["Merge", "Quick"])
        },
        "compute_answer": lambda params: "B. O(n log n)",
        "options": [
            "A. O(n)",
            "B. O(n log n)",
            "C. O(n²)",
            "D. O(log n)"
        ]
    },
    {
        "template": Template("A SQL query selects rows from a table with {{n}} rows where a column value is greater than {{val}}. How many rows are returned?"),
        "difficulty": "beginner",
        "topic": "Databases",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "n": np.random.randint(10, 50),
            "val": np.random.randint(1, 5)
        },
        "compute_answer": lambda params: f"{max(0, params['n'] - params['val']):.0f}",
        "options": []
    },
    {
        "template": Template("What does the CAP theorem stand for in distributed systems?"),
        "difficulty": "advanced",
        "topic": "System Design",
        "goal": "Amazon SDE",
        "generate_params": lambda: {},
        "compute_answer": lambda params: "A. Consistency, Availability, Partition tolerance",
        "options": [
            "A. Consistency, Availability, Partition tolerance",
            "B. Consistency, Accuracy, Performance",
            "C. Concurrency, Availability, Performance",
            "D. Consistency, Atomicity, Partition tolerance"
        ]
    },
    {
        "template": Template("The HTTP status code {{code}} indicates:"),
        "difficulty": "intermediate",
        "topic": "Web Development",
        "goal": "Amazon SDE",
        "generate_params": lambda: {
            "code": random.choice([200, 404, 500])
        },
        "compute_answer": lambda params: "OK" if params["code"] == 200 else "Not Found" if params["code"] == 404 else "Internal Server Error",
        "options": []
    },
    # CAT Templates (Existing)
    {
        "template": Template("What is the simple interest on ${{P}} at {{r}}% per annum for {{t}} years?"),
        "difficulty": "beginner",
        "topic": "Quantitative Ability - Interest",
        "goal": "CAT",
        "generate_params": lambda: {
            "P": np.random.randint(500, 2000),
            "r": np.random.randint(2, 10),
            "t": np.random.randint(1, 5)
        },
        "compute_answer": lambda params: f"${(params['P'] * params['r'] * params['t'] / 100):.2f}",
        "options": []
    },
    {
        "template": Template("Solve for x: {{a}}x + {{b}} = {{c}}."),
        "difficulty": "intermediate",
        "topic": "Quantitative Ability - Algebra",
        "goal": "CAT",
        "generate_params": lambda: {
            "a": np.random.randint(2, 6),
            "b": np.random.randint(1, 10),
            "c": np.random.randint(10, 20)
        },
        "compute_answer": lambda params: f"B. {(params['c'] - params['b']) / params['a']:.0f}",
        "options": lambda params: [
            f"A. {((params['c'] - params['b']) / params['a'] - 1):.0f}",
            f"B. {((params['c'] - params['b']) / params['a']):.0f}",
            f"C. {((params['c'] - params['b']) / params['a'] + 1):.0f}",
            f"D. {((params['c'] - params['b']) / params['a'] + 2):.0f}"
        ]
    },
    {
        "template": Template("Find the area of a triangle with base {{b}} cm and height {{h}} cm."),
        "difficulty": "intermediate",
        "topic": "Quantitative Ability - Geometry",
        "goal": "CAT",
        "generate_params": lambda: {
            "b": np.random.randint(4, 10),
            "h": np.random.randint(5, 12)
        },
        "compute_answer": lambda params: f"{(0.5 * params['b'] * params['h']):.2f}",
        "options": []
    },
    {
        "template": Template("The total sales for company X in year {{year}} is (in thousands):"),
        "difficulty": "beginner",
        "topic": "Data Interpretation and Logical Reasoning - Data Interpretation",
        "goal": "CAT",
        "generate_params": lambda: {
            "year": np.random.randint(1, 5),
            "sales": np.random.randint(100, 400)
        },
        "compute_answer": lambda params: f"B. {params['sales']}",
        "options": lambda params: [
            f"A. {params['sales'] - 50}",
            f"B. {params['sales']}",
            f"C. {params['sales'] + 50}",
            f"D. {params['sales'] + 100}"
        ]
    },
    # CAT New Templates
    {
        "template": Template("The smallest number that leaves remainders {{r1}}, {{r2}} when divided by {{d1}}, {{d2}} respectively is:"),
        "difficulty": "intermediate",
        "topic": "Quantitative Ability - HCF and LCM",
        "goal": "CAT",
        "generate_params": lambda: {
            "r1": np.random.randint(1, 5),
            "r2": np.random.randint(1, 5),
            "d1": np.random.randint(5, 10),
            "d2": np.random.randint(5, 10)
        },
        "compute_answer": lambda params: f"B. {params['r1'] + params['d1'] * (params['r2'] - params['r1']) // np.gcd(params['d1'], params['d2'])}",
        "options": lambda params: [
            f"A. {params['r1'] + params['d1'] * (params['r2'] - params['r1']) // np.gcd(params['d1'], params['d2']) - 10}",
            f"B. {params['r1'] + params['d1'] * (params['r2'] - params['r1']) // np.gcd(params['d1'], params['d2'])}",
            f"C. {params['r1'] + params['d1'] * (params['r2'] - params['r1']) // np.gcd(params['d1'], params['d2']) + 10}",
            f"D. {params['r1'] + params['d1'] * (params['r2'] - params['r1']) // np.gcd(params['d1'], params['d2']) + 20}"
        ]
    },
    {
        "template": Template("The sum of the roots of the quadratic equation {{a}}x² + {{b}}x + {{c}} = 0 is:"),
        "difficulty": "advanced",
        "topic": "Quantitative Ability - Quadratic Equations",
        "goal": "CAT",
        "generate_params": lambda: {
            "a": np.random.randint(1, 5),
            "b": np.random.randint(-10, 10),
            "c": np.random.randint(-10, 10)
        },
        "compute_answer": lambda params: f"{(-params['b'] / params['a']):.2f}",
        "options": []
    },
    {
        "template": Template("In a seating arrangement, if A sits to the left of B and B sits to the right of C, who is in the middle?"),
        "difficulty": "beginner",
        "topic": "Data Interpretation and Logical Reasoning - Logical Reasoning",
        "goal": "CAT",
        "generate_params": lambda: {},
        "compute_answer": lambda params: "B. B",
        "options": [
            "A. A",
            "B. B",
            "C. C",
            "D. Cannot be determined"
        ]
    },
    {
        "template": Template("The probability of getting a {{event}} when rolling a fair six-sided die is (to two decimal places):"),
        "difficulty": "intermediate",
        "topic": "Quantitative Ability - Probability",
        "goal": "CAT",
        "generate_params": lambda: {
            "event": random.choice(["prime number", "even number"])
        },
        "compute_answer": lambda params: "0.50" if params["event"] == "even number" else "0.50",
        "options": []
    }
]
