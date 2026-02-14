import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# Add src to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(root_path / ".env")
except ImportError:
    pass

from agent.intent_recognizer import intent_recognizer

def run_tests():
    test_cases = [
        # --- asking_info cases (Should be asking_info) ---
        {"name": "Thai: Request Pictures", "msg": "ขอดูรูปที่พักหน่อย", "expected": "asking_info"},
        {"name": "Thai: Request Gallery", "msg": "มีแกลเลอรี่ภาพห้องพักไหม", "expected": "asking_info"},
        {"name": "Thai: Weather Question", "msg": "อากาศที่เกาะเต่าเป็นยังไงบ้างช่วงนี้", "expected": "asking_info"},
        {"name": "Thai: Boat Schedule", "msg": "เรือไปเกาะเต่ารอบสุดท้ายกี่โมง", "expected": "asking_info"},
        {"name": "Thai: Room Detail", "msg": "ห้อง S1 มีไดร์เป่าผมไหม", "expected": "asking_info"},
        {"name": "Thai: Policy Question", "msg": "ยกเลิกการจองต้องทำยังไง", "expected": "asking_info"},
        {"name": "English: Picture Request", "msg": "Can you show me some photos of the resort?", "expected": "asking_info"},
        {"name": "English: Weather", "msg": "Is it raining in Koh Tao now?", "expected": "asking_info"},

        # --- out_of_scope cases (Should be out_of_scope) ---
        {"name": "Thai: Irrelevant News", "msg": "วันนี้มีข่าวอะไรน่าสนใจบ้าง", "expected": "out_of_scope"},
        {"name": "Thai: Cooking Recipe", "msg": "วิธีทำผัดไทยทำยังไง", "expected": "out_of_scope"},
        {"name": "Thai: Tech Question", "msg": "สอนเขียน Python หน่อย", "expected": "out_of_scope"},
        {"name": "Thai: Gibberish", "msg": "asd fgh jkl", "expected": "out_of_scope"},
        {"name": "English: Politics", "msg": "Who is the president of USA?", "expected": "out_of_scope"},
        {"name": "English: Sports", "msg": "Who won the football match yesterday?", "expected": "out_of_scope"},

        # --- Boundary/Tricky cases ---
        {"name": "Thai: Island Activities (Borderline/In-scope)", "msg": "ไปดำน้ำที่เกาะเต่าที่ไหนดีที่สุด", "expected": "asking_info"}, # Should be in-scope for island info
        {"name": "Thai: General Greeting", "msg": "สวัสดีครับ", "expected": "greeting"},
        {"name": "Thai: Ambiguous 'Show me'", "msg": "ขอดูหน่อย", "history": [HumanMessage(content="ห้อง S1 สวยไหม")], "expected": "asking_info"}, # Context dependent
    ]

    passed = 0
    failed = []

    print(f"{'Test Case':<35} | {'Expected':<15} | {'Actual':<15} | {'Result'}")
    print("-" * 80)

    for case in test_cases:
        history = case.get("history", [])
        current_msg = HumanMessage(content=case["msg"])
        messages = history + [current_msg]
        
        state = {"messages": messages}
        try:
            result = intent_recognizer(state)
            actual = result.get("intent")
            
            status = "✅ PASS" if actual == case["expected"] else "❌ FAIL"
            print(f"{case['name']:<35} | {case['expected']:<15} | {actual:<15} | {status}")
            
            if actual == case["expected"]:
                passed += 1
            else:
                failed.append(case)
        except Exception as e:
            print(f"{case['name']:<35} | {case['expected']:<15} | ERROR           | ❌ FAIL ({e})")
            failed.append(case)

    print("-" * 80)
    print(f"Total: {len(test_cases)} | Passed: {passed} | Failed: {len(failed)}")
    
    if failed:
        print("\nFailed Cases Details:")
        for f in failed:
            print(f"- {f['name']}: '{f['msg']}' (Expected: {f['expected']})")

if __name__ == "__main__":
    run_tests()
