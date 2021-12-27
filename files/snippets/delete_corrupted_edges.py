# Delete corrupted edges in a workflow:
# - edges missing a source, destinaton or a workflow
# - edges whose source or destination is not in the workflow's services
# - duplicated edges i.e with same source, destination, workflow and subtype
# flake8: noqa

from collections import defaultdict

edges = set(db.fetch_all("workflow_edge"))
duplicated_edges, number_of_corrupted_edges = defaultdict(list), 0
for edge in list(edges):
    services = getattr(edge.workflow, "services", [])
    if (
        not edge.source
        or not edge.destination
        or not edge.workflow
        or edge.source not in services
        or edge.destination not in services
    ):
        edges.remove(edge)
        db.session.delete(edge)
        number_of_corrupted_edges += 1
db.session.commit()
for edge in edges:
    duplicated_edges[
        (
            edge.source.name,
            edge.destination.name,
            edge.workflow.name,
            edge.subtype,
        )
    ].append(edge)
for duplicates in duplicated_edges.values():
    for duplicate in duplicates[1:]:
        db.session.delete(duplicate)
        number_of_corrupted_edges += 1

print(f"Number of corrupted edges deleted: {number_of_corrupted_edges}")
