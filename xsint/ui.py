def print_results(report):
    results = report.get("results", [])
    target_type = str(report.get("type", "unknown")).upper()
    error = report.get("error")

    if error:
        print(f"type   : {target_type}")
        print("status : aborted")
        print(f"error  : {error}")
        return

    if not results:
        print(f"type     : {target_type}")
        print("status   : completed")
        print("findings : 0")
        return

    groups = {}
    for item in results:
        groups.setdefault(item.get("source", "unknown"), []).append(item)

    print(f"type     : {target_type}")
    print(f"findings : {len(results)}")
    print(f"sources  : {len(groups)}")
    print()

    for source in sorted(groups):
        items = groups[source]
        print(f"{source} ({len(items)})")
        max_label = max(len(_label(i)) for i in items)
        for item in items:
            label = _label(item).ljust(max_label)
            value = str(item.get("value", "N/A"))
            print(f"  {label} : {value}")
        print()


def _label(item):
    label = str(item.get("label", "N/A"))
    group = item.get("group")
    return f"{group} / {label}" if group else label
