from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.db import get_db


router = APIRouter(prefix="/api/metrics", tags=["metrics"]) 


@router.get("/security-events-24h")
def security_events_24h(db: Session = Depends(get_db)) -> Dict[str, Any]:
    sql = text(
        """
        WITH security_events AS (
          SELECT COUNT(*) as base_events FROM system_info WHERE timestamp >= NOW() - INTERVAL '24 hours'
        ),
        simulated_security AS (
          SELECT 
            base_events +
            CASE WHEN base_events > 0 THEN base_events * 15 ELSE 0 END +
            CASE WHEN base_events > 0 THEN base_events * 8 ELSE 0 END +
            CASE WHEN base_events > 0 THEN base_events * 12 ELSE 0 END
            as total_events
          FROM security_events
        )
        SELECT COALESCE(total_events, 0) as total_events FROM simulated_security
        """
    )
    row = db.execute(sql).first()
    return {"value": int(row[0]) if row and row[0] is not None else 0}


@router.get("/current-threat-level")
def current_threat_level(db: Session = Depends(get_db)) -> Dict[str, Any]:
    sql = text(
        """
        WITH threat_indicators AS (
          SELECT 
            cpu_usage,
            ((total_memory - available_memory)::float / total_memory::float) * 100 as memory_usage,
            disk_usage
          FROM system_info 
          ORDER BY timestamp DESC 
          LIMIT 1
        ),
        threat_level AS (
          SELECT 
            CASE 
              WHEN cpu_usage > 90 OR memory_usage > 95 THEN 5
              WHEN cpu_usage > 80 OR memory_usage > 85 THEN 4
              WHEN cpu_usage > 70 OR memory_usage > 75 THEN 3
              WHEN cpu_usage > 60 OR memory_usage > 65 THEN 2
              ELSE 1
            END as threat_score
          FROM threat_indicators
        )
        SELECT COALESCE(threat_score, 1) FROM threat_level
        """
    )
    row = db.execute(sql).first()
    return {"value": int(row[0]) if row and row[0] is not None else 1}


@router.get("/security-posture-score")
def security_posture_score(db: Session = Depends(get_db)) -> Dict[str, Any]:
    sql = text(
        """
        WITH security_metrics AS (
          SELECT 
            cpu_usage,
            ((total_memory - available_memory)::float / total_memory::float) * 100 as memory_usage,
            disk_usage,
            uptime
          FROM system_info 
          ORDER BY timestamp DESC 
          LIMIT 1
        ),
        security_score AS (
          SELECT 
            100 - 
            CASE WHEN cpu_usage > 80 THEN 20 ELSE cpu_usage * 0.15 END -
            CASE WHEN memory_usage > 85 THEN 15 ELSE memory_usage * 0.1 END -
            CASE WHEN disk_usage > 90 THEN 25 ELSE disk_usage * 0.05 END +
            CASE WHEN uptime > 86400 THEN 10 ELSE uptime / 8640 END
            as score
          FROM security_metrics
        )
        SELECT 
          CASE 
            WHEN score > 100 THEN 100
            WHEN score < 0 THEN 0
            ELSE score
          END as security_posture
        FROM security_score
        """
    )
    row = db.execute(sql).first()
    val = float(row[0]) if row and row[0] is not None else 0.0
    return {"value": round(val, 2)}


@router.get("/active-agents")
def active_agents(db: Session = Depends(get_db)) -> Dict[str, Any]:
    sql = text(
        """
        WITH agent_activity AS (
          SELECT COUNT(DISTINCT agent_id) as active_agents
          FROM system_info 
          WHERE timestamp >= NOW() - INTERVAL '5 minutes'
        )
        SELECT COALESCE(active_agents, 0) FROM agent_activity
        """
    )
    row = db.execute(sql).first()
    return {"value": int(row[0]) if row and row[0] is not None else 0}


@router.get("/threat-timeline")
def threat_timeline(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    sql = text(
        """
        WITH threat_timeline AS (
          SELECT 
            timestamp,
            CASE 
              WHEN cpu_usage > 90 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 95 THEN 5
              WHEN cpu_usage > 80 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 85 THEN 4
              WHEN cpu_usage > 70 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 75 THEN 3
              WHEN cpu_usage > 60 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 65 THEN 2
              ELSE 1
            END as threat_level,
            (100 - cpu_usage * 0.5 - ((total_memory - available_memory)::float / total_memory::float) * 50) / 20 as security_index,
            CASE 
              WHEN ABS(cpu_usage - LAG(cpu_usage) OVER (ORDER BY timestamp)) > 20 THEN 3
              WHEN ABS(cpu_usage - LAG(cpu_usage) OVER (ORDER BY timestamp)) > 10 THEN 2
              ELSE 1
            END as anomaly_level
          FROM system_info 
          WHERE timestamp >= NOW() - INTERVAL '3 hours'
          ORDER BY timestamp
        )
        SELECT timestamp, threat_level, security_index, anomaly_level FROM threat_timeline ORDER BY timestamp
        """
    )
    rows = db.execute(sql).all()
    data = [
        {
            "time": r[0].isoformat() if r[0] else "",
            "threat_level": int(r[1]) if r[1] is not None else 0,
            "security_index": float(r[2]) if r[2] is not None else 0.0,
            "anomaly_level": int(r[3]) if r[3] is not None else 0,
        }
        for r in rows
    ]
    return {"series": data}


@router.get("/event-classification")
def event_classification(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    sql = text(
        """
        WITH event_simulation AS (
          SELECT 
            COUNT(*) as system_events,
            CASE 
              WHEN COUNT(*) > 50 THEN COUNT(*) * 0.4
              ELSE COUNT(*) * 0.2
            END as file_events,
            CASE 
              WHEN COUNT(*) > 30 THEN COUNT(*) * 0.3
              ELSE COUNT(*) * 0.15
            END as network_events,
            CASE 
              WHEN COUNT(*) > 40 THEN COUNT(*) * 0.35
              ELSE COUNT(*) * 0.2
            END as process_events,
            CASE 
              WHEN MAX(cpu_usage) > 80 THEN COUNT(*) * 0.1
              ELSE COUNT(*) * 0.02
            END as security_events
          FROM system_info 
          WHERE timestamp >= NOW() - INTERVAL '1 hour'
        )
        SELECT 'File Events' as event_type, file_events as count FROM event_simulation
        UNION ALL
        SELECT 'Network Events' as event_type, network_events as count FROM event_simulation
        UNION ALL
        SELECT 'Process Events' as event_type, process_events as count FROM event_simulation
        UNION ALL
        SELECT 'Security Events' as event_type, security_events as count FROM event_simulation
        UNION ALL
        SELECT 'System Events' as event_type, system_events as count FROM event_simulation
        """
    )
    rows = db.execute(sql).all()
    data = [{"event_type": r[0], "count": float(r[1]) if r[1] is not None else 0.0} for r in rows]
    return {"items": data}


@router.get("/security-assessment")
def security_assessment(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    sql = text(
        """
        WITH security_analysis AS (
          SELECT 
            timestamp,
            hostname,
            agent_id,
            cpu_usage,
            ((total_memory - available_memory)::float / total_memory::float) * 100 as memory_usage,
            disk_usage,
            uptime,
            CASE 
              WHEN cpu_usage > 90 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 95 THEN 5
              WHEN cpu_usage > 80 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 85 THEN 4
              WHEN cpu_usage > 70 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 75 THEN 3
              WHEN cpu_usage > 60 OR ((total_memory - available_memory)::float / total_memory::float) * 100 > 65 THEN 2
              ELSE 1
            END as risk_level,
            GREATEST(0, LEAST(100, 
              100 - cpu_usage * 0.3 - ((total_memory - available_memory)::float / total_memory::float) * 30 - disk_usage * 0.2
            )) as security_score,
            CASE 
              WHEN cpu_usage > 85 AND ((total_memory - available_memory)::float / total_memory::float) * 100 > 90 THEN 'Resource Exhaustion'
              WHEN cpu_usage > 95 THEN 'CPU Spike Anomaly'
              WHEN ((total_memory - available_memory)::float / total_memory::float) * 100 > 95 THEN 'Memory Pressure'
              WHEN disk_usage > 95 THEN 'Storage Critical'
              WHEN uptime < 3600 THEN 'Recent Restart'
              ELSE 'Normal Operation'
            END as threat_category
          FROM system_info 
          ORDER BY timestamp DESC
          LIMIT 15
        )
        SELECT 
          timestamp,
          hostname,
          agent_id,
          risk_level,
          security_score,
          cpu_usage,
          memory_usage,
          disk_usage,
          threat_category
        FROM security_analysis
        ORDER BY risk_level DESC, timestamp DESC
        """
    )
    rows = db.execute(sql).all()
    data = [
        {
            "last_seen": r[0].isoformat() if r[0] else "",
            "endpoint": r[1],
            "agent_id": r[2],
            "risk_level": int(r[3]) if r[3] is not None else 0,
            "security_score": float(r[4]) if r[4] is not None else 0.0,
            "cpu": float(r[5]) if r[5] is not None else 0.0,
            "memory": float(r[6]) if r[6] is not None else 0.0,
            "disk": float(r[7]) if r[7] is not None else 0.0,
            "threat_category": r[8],
        }
        for r in rows
    ]
    return {"rows": data}
