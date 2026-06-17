# tools/similarity_search.py
from __future__ import annotations
from typing import Any, Dict, List

_DEMO_EVENTS = [
    {"id":"COMP-2025-088","complaint_id":"COMP-2025-088","event_type":"COMPLAINT","product":"Demo-Parenteral","lot_number":"LOT-2025-088","site":"SITE-MFG-01","severity":"MAJOR","description":"Visible particulate matter in vial batch.","root_cause":"Inadequate filter integrity testing before filling run.","capa_id":"CAPA-2025-088","capa_status":"CLOSED","score":0.91,"similarity_score":0.91},
    {"id":"COMP-2025-102","complaint_id":"COMP-2025-102","event_type":"DEVIATION","product":"Demo-Parenteral","lot_number":"LOT-2025-102","site":"SITE-MFG-01","severity":"MAJOR","description":"Particle contamination detected during filling line operation.","root_cause":"Filter integrity test not performed prior to production batch.","capa_id":"CAPA-2025-102","capa_status":"CLOSED","score":0.87,"similarity_score":0.87},
    {"id":"COMP-2024-201","complaint_id":"COMP-2024-201","event_type":"DEVIATION","product":"Demo-Parenteral","lot_number":"LOT-2024-201","site":"SITE-MFG-01","severity":"CRITICAL","description":"Foreign particle identified in injectable product; lot recalled.","root_cause":"Environmental contamination breach during gowning procedure.","capa_id":"CAPA-2024-201","capa_status":"CLOSED","score":0.75,"similarity_score":0.75},
]

_TEMPERATURE_EVENTS = [
    {"id":"COMP-2025-045","complaint_id":"COMP-2025-045","event_type":"DEVIATION","product":"Demo-Tablet","lot_number":"LOT-2025-045","site":"SITE-MFG-02","severity":"MINOR","description":"Temperature excursion in storage area over weekend, 4-hour event.","root_cause":"Alarm threshold configuration error in monitoring system.","capa_id":"CAPA-2025-045","capa_status":"CLOSED","score":0.88,"similarity_score":0.88},
    {"id":"COMP-2025-067","complaint_id":"COMP-2025-067","event_type":"DEVIATION","product":"Demo-Tablet","lot_number":"LOT-2025-067","site":"SITE-MFG-02","severity":"MINOR","description":"HVAC failure caused brief temperature excursion in secondary packaging area.","root_cause":"Preventive maintenance schedule not adhered to for HVAC unit.","capa_id":"CAPA-2025-067","capa_status":"OPEN","score":0.79,"similarity_score":0.79},
]


def _select_demo_events(query):
    desc = (query.get("description") or "").lower()
    if any(kw in desc for kw in ["particulate", "particle", "contamination"]):
        return _DEMO_EVENTS
    if any(kw in desc for kw in ["temperature", "excursion", "hvac", "storage"]):
        return _TEMPERATURE_EVENTS
    return _DEMO_EVENTS[:1]


def search_similar_demo(query):
    """Demo similarity search. Returns fixture events. All numbers from fixture."""
    return _select_demo_events(query)


def cluster_events(events):
    """Group similar events into thematic clusters."""
    if not events:
        return []
    filter_c, env_c, temp_c, misc = [], [], [], []
    for e in events:
        rc = (e.get("root_cause") or "").lower()
        if "filter" in rc:
            filter_c.append(e)
        elif "environmental" in rc or "gown" in rc:
            env_c.append(e)
        elif "temperature" in rc or "hvac" in rc or "alarm" in rc:
            temp_c.append(e)
        else:
            misc.append(e)
    clusters = []
    if filter_c:
        clusters.append({"cluster_id":"CLU-FILTER","theme":"filter integrity testing gap","count":len(filter_c),"event_ids":[e.get("id") or e.get("complaint_id") for e in filter_c],"recurrence_risk":"HIGH"})
    if env_c:
        clusters.append({"cluster_id":"CLU-ENV","theme":"environmental contamination control breach","count":len(env_c),"event_ids":[e.get("id") or e.get("complaint_id") for e in env_c],"recurrence_risk":"HIGH"})
    if temp_c:
        clusters.append({"cluster_id":"CLU-TEMP","theme":"temperature monitoring and control gap","count":len(temp_c),"event_ids":[e.get("id") or e.get("complaint_id") for e in temp_c],"recurrence_risk":"MEDIUM"})
    if misc:
        clusters.append({"cluster_id":"CLU-MISC","theme":"miscellaneous under investigation","count":len(misc),"event_ids":[e.get("id") or e.get("complaint_id") for e in misc],"recurrence_risk":"UNKNOWN"})
    return clusters
