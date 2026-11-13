from typing import Any, Dict, Iterable, List, Set

class ForwardChaining:

    def __init__(self, rules: List[Dict[str, Any]]) -> None:
        self.rules = rules

    @staticmethod
    def _is_rule_satisfied(rule: Dict[str, Any], working_memory: Set[str]) -> bool:
        premises = rule.get("premises", [])
        operator = rule.get("operator", "AND").upper()

        if not premises:
            return False

        if operator == "AND":
            return all(premise in working_memory for premise in premises)
        if operator == "OR":
            return any(premise in working_memory for premise in premises)

        raise ValueError(
            f"Operator '{operator}' pada aturan {rule.get('id', '?')} tidak didukung. "
            "Gunakan AND atau OR."
        )

    def run(self, initial_facts: Iterable[str]) -> Dict[str, Any]:
        initial_facts = set(initial_facts)
        working_memory: Set[str] = set(initial_facts)
        fired_rules: List[Dict[str, Any]] = []
        fired_rule_ids: Set[str] = set()
        derivations: Dict[str, Dict[str, Any]] = {}

        while True:
            new_fact_added = False

            for rule in self.rules:
                rule_id = rule["id"]
                if rule_id in fired_rule_ids:
                    continue

                if not self._is_rule_satisfied(rule, working_memory):
                    continue

                fired_rule_ids.add(rule_id)
                fired_rules.append(rule)

                conclusion = rule["conclusion"]
                if conclusion not in working_memory:
                    working_memory.add(conclusion)
                    derivations[conclusion] = rule
                    new_fact_added = True

            # Ulangi pemeriksaan jika pada putaran ini ada fakta baru.
            if not new_fact_added:
                break

        return {
            "working_memory": working_memory,
            "fired_rules": fired_rules,
            "derivations": derivations,
            "initial_facts": initial_facts,
        }
