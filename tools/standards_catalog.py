"""get_nc_standards tool.

Returns the NC DPI standards catalog (and topic cluster shortcuts) for
display to the student or parent.
"""

from _sdk import function_tool
from standards.nc_standards import NC_STANDARDS, TOPIC_CLUSTERS


def get_nc_standards_impl(grade_filter: str = "all") -> list[dict]:
    """Plain callable used by the tool wrapper below and directly in tests."""
    grade_filter = (grade_filter or "all").strip().lower()
    if grade_filter not in ("5", "6", "all"):
        grade_filter = "all"

    results = []
    for code, info in NC_STANDARDS.items():
        if grade_filter != "all" and info["grade"] != grade_filter:
            continue
        results.append(
            {
                "code": code,
                "grade": info["grade"],
                "domain": info["domain"],
                "description": info["description"],
            }
        )

    if grade_filter == "all":
        results.append(
            {
                "code": "clusters",
                "grade": "all",
                "domain": "Topic Cluster Shortcuts",
                "description": ", ".join(TOPIC_CLUSTERS.keys()),
            }
        )

    return results


@function_tool
def get_nc_standards(grade_filter: str = "all") -> list[dict]:
    """Return the NC DPI 5th/6th grade standards catalog, optionally filtered by grade."""
    return get_nc_standards_impl(grade_filter)
