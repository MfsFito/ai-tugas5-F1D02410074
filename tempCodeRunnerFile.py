
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