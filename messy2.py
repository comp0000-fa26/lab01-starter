def process(lines):

#Do everything in one place:
#- Parse each comma-separated line into id(int), name(stripped), score(float)
#- Ignore blank/whitespace-only lines
#- Keep only records with score >= 60.0
#- Return {"count": , "mean_score": <avg_of_passing_or_0.0>}

    # messy state
    a = [] # will hold parsed records as dicts
    b = 0 # count of passing
    c = 0.0 # sum of passing scores

    if lines is None:
        lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line is None:
            i += 1
            continue
        s = line.strip()
        if s == "":
            i += 1
            continue
        # split (don’t validate too much, skip if malformed)
        parts = s.split(",")
        if len(parts) < 3:
            i += 1
            continue
        # parse with extra strip on each field
        p0 = parts[0].strip()
        p1 = parts[1].strip()
        # if there are more than 3 fields, just use the first three
        p2 = parts[2].strip()
        try:
            _id = int(p0)
        except Exception:
            # if id isn’t int, skip
            i += 1
            continue
        try:
            _score = float(p2)
        except Exception:
            i += 1
            continue
        _name = p1  # already stripped

        # store (even though we only need passing for the final summary)
        a.append({"id": _id, "name": _name, "score": _score})

        # filter passing (>= 60.0)
        # do the threshold here instead of a separate pass
        if _score >= 60.0:
            b = b + 1
            c = c + _score

        i += 1

    # compute summary of passing
    if b == 0:
        # mean score is 0.0 when no passing records
        return {"count": 0, "mean_score": 0.0}
    # avoid integer division worries; c is float already
    m = c / float(b)
    # return the summary only (ignore the full records we built)
    return {"count": b, "mean_score": m}