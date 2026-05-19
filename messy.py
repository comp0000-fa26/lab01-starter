def process(lines):
    records = []
    for line in lines:
        fields = line.split(",")
        if len(fields) >= 3:
            records.append({
                "id": int(fields[0]),
                "name": fields[1].strip(),
                "score": float(fields[2])
            })
    passing = [r for r in records if r["score"] >= 60.0]
    summary = {
        "count": len(passing),
        "mean_score": sum(r["score"] for r in passing) / len(passing)
    }
    return summary
