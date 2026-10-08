import os
import sys
import json

# Add parent directory to path to enable app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.services.llm_service import extract_job_requirements, verify_generated_answer


def run_evaluation():
    """
    Evaluation runner to benchmark AI skill extraction and claim verification accuracy.
    """
    test_cases_file = os.path.join(os.path.dirname(__file__), "test_cases.json")
    if not os.path.exists(test_cases_file):
        print(f"[ERROR] Test cases file not found: {test_cases_file}")
        return

    with open(test_cases_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 60)
    print("      AI JOB APPLICATION AGENT — EVALUATION SUITE")
    print("=" * 60)

    passed = 0
    total = len(cases)

    for case in cases:
        print(f"\nRunning Test [{case['id']}]: {case['name']}...")
        
        try:
            if "job_description" in case and "expected_skills" in case:
                # Skill extraction test
                result = extract_job_requirements(case["job_description"])
                extracted = set(s.lower() for s in result.get("required_skills", []))
                expected = set(s.lower() for s in case["expected_skills"])
                
                overlap = extracted.intersection(expected)
                accuracy = len(overlap) / len(expected) if expected else 1.0

                if accuracy >= 0.5:
                    print(f"  [PASS] Extracted skills: {result.get('required_skills')}")
                    passed += 1
                else:
                    print(f"  [FAIL] Expected skills {case['expected_skills']} but got {result.get('required_skills')}")

            elif "answer_text" in case and "expected_verified" in case:
                # Verification test
                res = verify_generated_answer(
                    answer_text=case["answer_text"],
                    resume_text=case["resume_text"]
                )
                verified = res.get("verified")
                expected_verified = case["expected_verified"]

                if verified == expected_verified:
                    print(f"  [PASS] Verified status: {verified} (Expected: {expected_verified})")
                    if res.get("issues"):
                        print(f"         Issues flagged: {res.get('issues')}")
                    passed += 1
                else:
                    print(f"  [FAIL] Expected verified={expected_verified} but got {verified}.")
                    print(f"         Details: {res}")

        except Exception as e:
            print(f"  [ERROR] Execution exception: {e}")

    print("\n" + "=" * 60)
    print(f" SUMMARY: {passed}/{total} tests passed ({int(passed/total*100)}% accuracy)")
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()
