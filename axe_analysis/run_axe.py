from axe_selenium_python import Axe
import json

def run_axe_analysis(driver):
    axe = Axe(driver)
    try:
        axe.inject()
        results = axe.run()
    except Exception as e:
        print(f"Error ejecutando Axe: {e}")
        return []

    violations = results.get("violations", [])
    wcag_tags = {"wcag2a", "wcag21a", "wcag22a"}
    filtered_violations = [v for v in violations if wcag_tags.intersection(v.get("tags", []))]

    with open("accessibility_violations.json", "w", encoding="utf-8") as f:
        json.dump(filtered_violations, f, indent=4, ensure_ascii=False)

    return filtered_violations
