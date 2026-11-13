import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from forward_chaining import ForwardChaining


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_FILE = BASE_DIR / "knowledge_base.json"


def load_knowledge_base(file_path: Path = KNOWLEDGE_BASE_FILE) -> Dict[str, Any]:
    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"File basis pengetahuan tidak ditemukan: {file_path}\n"
            "Pastikan knowledge_base.json berada satu folder dengan main.py."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Format JSON tidak valid pada baris {exc.lineno}, kolom {exc.colno}: {exc.msg}"
        ) from exc

    required_sections = ("project", "sources", "facts", "conclusions", "rules")
    for section in required_sections:
        if section not in data:
            raise ValueError(f"Bagian '{section}' tidak ditemukan di knowledge_base.json.")

    fact_ids = [item["id"] for item in data["facts"]]
    conclusion_ids = [item["id"] for item in data["conclusions"]]
    rule_ids = [item["id"] for item in data["rules"]]
    source_ids = [item["id"] for item in data["sources"]]

    for label, values in (
        ("fakta", fact_ids),
        ("kesimpulan", conclusion_ids),
        ("aturan", rule_ids),
        ("sumber", source_ids),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"Terdapat ID {label} yang duplikat di knowledge_base.json.")

    known_premises = set(fact_ids) | set(conclusion_ids)
    known_conclusions = set(conclusion_ids)
    known_sources = set(source_ids)

    for rule in data["rules"]:
        if not rule.get("premises"):
            raise ValueError(f"Aturan {rule.get('id', '?')} tidak memiliki premises.")
        if rule.get("operator", "AND").upper() not in ("AND", "OR"):
            raise ValueError(f"Operator pada aturan {rule.get('id', '?')} harus AND atau OR.")
        if rule.get("conclusion") not in known_conclusions:
            raise ValueError(
                f"Kesimpulan pada aturan {rule.get('id', '?')} tidak ditemukan di bagian conclusions."
            )

        for premise in rule["premises"]:
            if premise not in known_premises:
                raise ValueError(
                    f"Premis '{premise}' pada aturan {rule.get('id', '?')} tidak dikenal."
                )

        for source_id in rule.get("source_ids", []):
            if source_id not in known_sources:
                raise ValueError(
                    f"Sumber '{source_id}' pada aturan {rule.get('id', '?')} tidak ditemukan."
                )

    return data


def ask_yes_no_unknown(fact: Dict[str, Any], number: int, total: int) -> str:
    print("\n" + "-" * 68)
    print(f"PERTANYAAN {number}/{total} — {fact['label']}")
    print(fact["question"])

    if fact.get("how_to_check"):
        print(f"Cara memeriksa: {fact['how_to_check']}")
    if fact.get("evidence_command"):
        print(f"Petunjuk/perintah: {fact['evidence_command']}")

    while True:
        answer = input("Jawaban [Y=Ya / T=Tidak / B=Belum tahu]: ").strip().lower()
        if answer in ("y", "ya", "yes"):
            return "yes"
        if answer in ("t", "tidak", "no", "n"):
            return "no"
        if answer in ("b", "belum", "belum tahu", "unknown", "?"):
            return "unknown"
        if answer == "":
            print("Jawaban kosong dianggap 'Belum tahu'.")
            return "unknown"
        print("Masukkan Y, T, atau B.")


def display_term(
    term_id: str,
    facts_by_id: Dict[str, Dict[str, Any]],
    conclusions_by_id: Dict[str, Dict[str, Any]],
) -> str:
    if term_id in facts_by_id:
        return facts_by_id[term_id]["label"]
    if term_id in conclusions_by_id:
        return conclusions_by_id[term_id]["label"]
    return term_id


def display_results(data: Dict[str, Any], result: Dict[str, Any]) -> None:
    facts_by_id = {item["id"]: item for item in data["facts"]}
    conclusions_by_id = {item["id"]: item for item in data["conclusions"]}
    sources_by_id = {item["id"]: item for item in data["sources"]}

    print("\n" + "=" * 68)
    print("HASIL PROSES FORWARD CHAINING")
    print("=" * 68)

    initial_facts = result["initial_facts"]
    if initial_facts:
        print("\nFakta awal yang dijawab YA:")
        for fact_id in sorted(initial_facts):
            print(f"  - {display_term(fact_id, facts_by_id, conclusions_by_id)} ({fact_id})")
    else:
        print("\nTidak ada fakta awal yang dijawab YA.")

    if not result["fired_rules"]:
        print("\nBelum ada aturan yang cocok dengan fakta yang diberikan.")
        print(
            "Sistem belum dapat menghasilkan kesimpulan. Periksa kembali kondisi yang "
            "dialami atau jawab pertanyaan yang sebelumnya masih 'Belum tahu'."
        )
        return

    print("\nATURAN YANG TERPAKAI:")
    for rule in result["fired_rules"]:
        print("\n" + "-" * 68)
        print(f"{rule['id']} — {rule['name']}")
        print("IF:")

        for premise in rule["premises"]:
            label = display_term(premise, facts_by_id, conclusions_by_id)
            if premise in result["derivations"]:
                previous_rule = result["derivations"][premise]
                origin = f"hasil kesimpulan aturan {previous_rule['id']}"
            elif premise in initial_facts:
                origin = "fakta awal dari jawaban pengguna: YA"
            else:
                origin = "fakta dalam Working Memory"
            print(f"  - {label} [{origin}]")

        conclusion_id = rule["conclusion"]
        conclusion_label = display_term(
            conclusion_id, facts_by_id, conclusions_by_id
        )
        print(f"THEN: {conclusion_label}")
        print(f"Penjelasan: {rule.get('explanation', '-')}")
        print(f"Rekomendasi: {rule.get('recommendation', '-')}")

        rule_sources = rule.get("source_ids", [])
        if rule_sources:
            print("Sumber aturan:")
            for source_id in rule_sources:
                source = sources_by_id[source_id]
                print(f"  - [{source_id}] {source['title']}: {source['url']}")

    print("\n" + "=" * 68)
    print("KESIMPULAN YANG DIHASILKAN")
    print("=" * 68)

    found_conclusions = [
        conclusion
        for conclusion in data["conclusions"]
        if conclusion["id"] in result["working_memory"]
    ]

    if not found_conclusions:
        print("Tidak ada kesimpulan yang dihasilkan.")
    else:
        for number, conclusion in enumerate(found_conclusions, start=1):
            print(f"{number}. {conclusion['label']}")
            print(f"   {conclusion['description']}")


def main() -> None:
    try:
        data = load_knowledge_base()
    except (FileNotFoundError, ValueError) as error:
        print(f"Gagal memuat basis pengetahuan: {error}")
        sys.exit(1)

    project_title = data["project"].get("title", "Sistem Pakar Git Merge")
    print("=" * 68)
    print(project_title)
    print("Metode inferensi: Forward Chaining")
    print("=" * 68)
    print(
        "Petunjuk: jawab Y untuk Ya, T untuk Tidak, atau B untuk Belum tahu.\n"
        "Program hanya mencatat jawaban YA sebagai fakta positif.\n"
        "Program tidak menjalankan perintah Git atau mengubah repository kamu."
    )

    initial_facts: List[str] = []
    facts = data["facts"]

    for index, fact in enumerate(facts, start=1):
        answer = ask_yes_no_unknown(fact, index, len(facts))
        if answer == "yes":
            initial_facts.append(fact["id"])

    engine = ForwardChaining(data["rules"])
    result = engine.run(initial_facts)
    display_results(data, result)

    print("\nSelesai. Terima kasih sudah menggunakan sistem pakar ini.")


if __name__ == "__main__":
    main()