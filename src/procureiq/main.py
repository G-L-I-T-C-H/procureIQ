#!/usr/bin/env python
import re
import sys
import warnings
from datetime import datetime, timedelta
from procureiq.crew import Procureiq
from procureiq.tools.supplier_search_tool import SupplierSearchTool

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

required_fields = ["topic", "rfq_number", "issue_date", "submission_deadline", "issued_by", "contact_person", "email", "phone"]

def get_validated_inputs():
    required_fields = {
        "what_to_acquire": None,
        "how_much": None,
        "deadline": None,
        "warranty": None
    }

    def extract_fields(user_input):
        what = re.search(r"\b(computers?|laptops?|desktops?|printers?|monitors?|devices?|items?)\b", user_input, re.I)
        how_much = re.search(r"\b\d+\b", user_input)
        deadline = re.search(r"(week|month|day|deadline|by \w+ \d{1,2})", user_input, re.I)
        warranty = re.search(r"\b\d+[- ]?(year|month)[s]?\b", user_input, re.I)

        return {
            "what_to_acquire": what.group(0) if what else None,
            "how_much": how_much.group(0) if how_much else None,
            "deadline": deadline.group(0) if deadline else None,
            "warranty": warranty.group(0) if warranty else None,
        }

    user_input = input("Enter your RFQ request (e.g., 'I need 50 laptops with a 3-year warranty in 2 weeks'): ")
    extracted = extract_fields(user_input)
    required_fields.update(extracted)

    for key, value in required_fields.items():
        if value is None:
            prompt = f"Please specify {key.replace('_', ' ')}: "
            required_fields[key] = input(prompt)

    topic = f"Initiate RFQ for {required_fields['how_much']} {required_fields['what_to_acquire']}. " \
            f"Include standard business specs, {required_fields['warranty']} warranty, and target {required_fields['deadline']} delivery."

    return topic

def run():
    topic = get_validated_inputs()
    today = datetime.now()
    two_weeks_from_now = today + timedelta(weeks=2)

    rfq_number = f"RFQ-{today.strftime('%Y%m%d')}-{str(today.microsecond)[-4:]}"
    issue_date = today.strftime("%Y-%m-%d")
    submission_deadline = two_weeks_from_now.strftime("%Y-%m-%d")

    inputs = {
        "topic": topic,
        "rfq_number": rfq_number,
        "issue_date": issue_date,
        "submission_deadline": submission_deadline,
        "issued_by": "SAP Labs India",
        "contact_person": "Sanjith.K",
        "email": "sanjithsap@sap.ac.in",
        "phone": "40989093874"
    }

    try:
        procureiq_instance = Procureiq()
        try:
            print(f"Agents config: {procureiq_instance.agents_config}")
        except AttributeError:
            raise ValueError("agents_config not initialized in Procureiq")
        if not procureiq_instance.agents_config.get('rfx_generator'):
            raise ValueError("Agent configuration for 'rfx_generator' not found in agents.yaml")
        if not procureiq_instance.agents_config.get('supplier_finder'):
            raise ValueError("Agent configuration for 'supplier_finder' not found in agents.yaml")

        # Execute the crew
        procureiq_instance.crew().kickoff(inputs=inputs)

        # Run the supplier search tool
        supplier_tool = SupplierSearchTool()
        result = supplier_tool.run(rfx_path="rfx.md")
        print(result)

    except ValueError as e:
        print(f"Validation error: {e}")
        print("Please update the 'topic' input in main.py with the missing information and rerun the script.")
        print("Previously provided input has been saved to partial_rfx_input.json and will be used in the next run.")
        raise
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def train():
    inputs = {
        "topic": "AI-Driven Procurement Automation",
        'current_year': str(datetime.now().year)
    }
    try:
        Procureiq().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    try:
        Procureiq().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    inputs = {
        "topic": "RFx Automation",
        "current_year": str(datetime.now().year)
    }
    try:
        Procureiq().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    run()