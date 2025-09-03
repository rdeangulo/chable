from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db import get_db
from app.utils import create_hubspot_contact, logger
from app.models import Thread, CustomerInfo, QualifiedLead, Conversation
import asyncio
import os

router = APIRouter()

@router.get("/test/hubspot")
async def test_hubspot_integration(db: Session = Depends(get_db)):
    """
    Test endpoint for HubSpot integration.
    Creates a test contact in HubSpot and returns the result.
    """
    # Test data
    test_customer = {
        "nombre": "Test Customer",
        "email": "test@example.com",
        "telefono": "+1234567890",
        "fuente": "Test",
        "ciudad_interes": "Test City",
        "tipo_propiedad": "Test Property",
        "presupuesto": "Test Budget"
    }
    
    try:
        # Try to create a contact
        contact_id = await create_hubspot_contact(test_customer)
        
        if contact_id:
            return {
                "success": True,
                "message": f"Successfully created HubSpot contact with ID: {contact_id}",
                "contact_id": contact_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to create HubSpot contact"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error testing HubSpot integration: {str(e)}"
        }


@router.get("/leads")
async def get_leads_by_source(
    source_type: str = Query(None, description="Filter by referral source type (e.g., 'ad', 'facebook', 'instagram')"),
    source_id: str = Query(None, description="Filter by specific referral source ID"),
    ctwa_clid: str = Query(None, description="Filter by Click to WhatsApp Click ID"),
    limit: int = Query(100, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Get leads filtered by referral source metadata.
    Useful for agencies to identify conversations started through their campaigns.
    """
    try:
        # Build query filters
        filters = []
        
        if source_type:
            filters.append(Thread.referral_source_type == source_type)
        
        if source_id:
            filters.append(Thread.referral_source_id == source_id)
            
        if ctwa_clid:
            filters.append(Thread.ctwa_clid == ctwa_clid)
        
        # Query threads with referral metadata
        query = db.query(Thread).filter(and_(*filters)) if filters else db.query(Thread)
        
        # Get threads with referral data
        threads_with_referral = query.filter(
            Thread.referral_source_type.isnot(None)
        ).limit(limit).all()
        
        # Get customer info for these threads
        results = []
        for thread in threads_with_referral:
            customer = db.query(CustomerInfo).filter_by(telefono=thread.sender).first()
            lead = db.query(QualifiedLead).filter_by(telefono=thread.sender).first()
            
            result = {
                "thread_id": thread.id,
                "sender": thread.sender,
                "sender_display_name": thread.sender_display_name,
                "platform": thread.sender_platform,
                "created_at": thread.created_at.isoformat() if thread.created_at else None,
                "last_conversation_at": thread.last_conversation_at.isoformat() if thread.last_conversation_at else None,
                "referral_metadata": {
                    "referral_source_type": thread.referral_source_type,
                    "referral_source_id": thread.referral_source_id,
                    "referral_source_url": thread.referral_source_url,
                    "referral_header": thread.referral_header,
                    "referral_body": thread.referral_body,
                    "ctwa_clid": thread.ctwa_clid,
                    "button_text": thread.button_text,
                    "button_payload": thread.button_payload,
                },
                "customer_info": {
                    "nombre": customer.nombre if customer else None,
                    "email": customer.email if customer else None,
                    "telefono": customer.telefono if customer else None,
                    "ciudad_interes": customer.ciudad_interes if customer else None,
                    "tipo_propiedad": customer.tipo_propiedad if customer else None,
                    "presupuesto_min": customer.presupuesto_min if customer else None,
                    "presupuesto_max": customer.presupuesto_max if customer else None,
                    "interes_compra": customer.interes_compra if customer else None,
                } if customer else None,
                "qualified_lead": {
                    "nombre": lead.nombre if lead else None,
                    "email": lead.email if lead else None,
                    "telefono": lead.telefono if lead else None,
                    "ciudad_interes": lead.ciudad_interes if lead else None,
                    "proyecto_interes": lead.proyecto_interes if lead else None,
                    "tipo_propiedad": lead.tipo_propiedad if lead else None,
                    "presupuesto_min": lead.presupuesto_min if lead else None,
                    "presupuesto_max": lead.presupuesto_max if lead else None,
                    "interes_compra": lead.interes_compra if lead else None,
                    "conversation_summary": lead.conversation_summary if lead else None,
                    "deducted_interest": lead.deducted_interest if lead else None,
                } if lead else None,
            }
            results.append(result)
        
        return {
            "success": True,
            "count": len(results),
            "leads": results,
            "filters_applied": {
                "source_type": source_type,
                "source_id": source_id,
                "ctwa_clid": ctwa_clid,
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error retrieving leads by source"
        }


@router.get("/leads/stats")
async def get_lead_source_stats(db: Session = Depends(get_db)):
    """
    Get statistics about lead sources and referral metadata.
    """
    try:
        from sqlalchemy import func
        
        # Get count by referral source type
        source_stats = db.query(
            Thread.referral_source_type,
            func.count(Thread.id).label('count')
        ).filter(
            Thread.referral_source_type.isnot(None)
        ).group_by(Thread.referral_source_type).all()
        
        # Get count by platform
        platform_stats = db.query(
            Thread.sender_platform,
            func.count(Thread.id).label('count')
        ).group_by(Thread.sender_platform).all()
        
        # Get total threads with referral data
        total_with_referral = db.query(Thread).filter(
            Thread.referral_source_type.isnot(None)
        ).count()
        
        # Get total threads
        total_threads = db.query(Thread).count()
        
        return {
            "success": True,
            "stats": {
                "total_threads": total_threads,
                "threads_with_referral_data": total_with_referral,
                "referral_data_percentage": round((total_with_referral / total_threads * 100) if total_threads > 0 else 0, 2),
                "by_source_type": [
                    {"source_type": stat.referral_source_type, "count": stat.count}
                    for stat in source_stats
                ],
                "by_platform": [
                    {"platform": stat.sender_platform, "count": stat.count}
                    for stat in platform_stats
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error retrieving lead source statistics"
        }


@router.get("/test/referral-metadata")
async def test_referral_metadata(db: Session = Depends(get_db)):
    """
    Test endpoint to check referral metadata functionality.
    """
    try:
        # Get a sample of threads with referral data
        threads_with_referral = db.query(Thread).filter(
            Thread.referral_source_type.isnot(None)
        ).limit(5).all()
        
        # Get total counts
        total_threads = db.query(Thread).count()
        threads_with_referral_count = db.query(Thread).filter(
            Thread.referral_source_type.isnot(None)
        ).count()
        
        # Get sample data
        sample_data = []
        for thread in threads_with_referral:
            sample_data.append({
                "sender": thread.sender,
                "created_at": thread.created_at.isoformat() if thread.created_at else None,
                "referral_source_type": thread.referral_source_type,
                "referral_source_id": thread.referral_source_id,
                "ctwa_clid": thread.ctwa_clid,
                "button_text": thread.button_text,
            })
        
        return {
            "success": True,
            "total_threads": total_threads,
            "threads_with_referral_data": threads_with_referral_count,
            "referral_data_percentage": round((threads_with_referral_count / total_threads * 100) if total_threads > 0 else 0, 2),
            "sample_data": sample_data,
            "message": "Check the logs for incoming webhook data to see referral metadata"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error testing referral metadata"
        }


@router.post("/leads/fix-missing")
async def fix_missing_leads(
    mode: str = Query("recent", description="Mode: 'recent' (last 7 days) or 'historical' (all time)"),
    days: int = Query(7, description="Number of days to look back for recent mode"),
    db: Session = Depends(get_db)
):
    """
    Fix missing leads by analyzing conversations that don't have qualified leads.
    """
    try:
        from app.utils import verify_and_fix_missing_leads
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not client:
            return {
                "success": False,
                "error": "OpenAI API key not found"
            }
        
        # Get threads without qualified leads
        if mode == "recent":
            from datetime import datetime, timedelta
            threshold_date = datetime.now() - timedelta(days=days)
            threads_without_leads = db.query(Thread).outerjoin(
                QualifiedLead, Thread.sender == QualifiedLead.telefono
            ).filter(
                QualifiedLead.id.is_(None),
                Thread.created_at >= threshold_date
            ).all()
        else:  # historical
            threads_without_leads = db.query(Thread).outerjoin(
                QualifiedLead, Thread.sender == QualifiedLead.telefono
            ).filter(
                QualifiedLead.id.is_(None)
            ).all()
        
        logger.info(f"Found {len(threads_without_leads)} threads without qualified leads")
        
        fixed_count = 0
        error_count = 0
        
        for thread in threads_without_leads:
            try:
                # Check if thread has conversations
                conversation_count = db.query(Conversation).filter_by(thread_id=thread.id).count()
                if conversation_count == 0:
                    continue
                
                # Try to fix missing lead
                lead_fixed = await verify_and_fix_missing_leads(client, db, thread)
                
                if lead_fixed:
                    fixed_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing thread {thread.sender}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Fixed {fixed_count} missing leads",
            "results": {
                "total_threads_processed": len(threads_without_leads),
                "leads_fixed": fixed_count,
                "errors": error_count,
                "mode": mode,
                "days": days if mode == "recent" else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error fixing missing leads: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error fixing missing leads"
        }


@router.get("/leads/coverage")
async def get_lead_coverage(db: Session = Depends(get_db)):
    """
    Get lead coverage statistics.
    """
    try:
        # Get total threads
        total_threads = db.query(Thread).count()
        
        # Get threads with qualified leads
        threads_with_leads = db.query(Thread).join(
            QualifiedLead, Thread.sender == QualifiedLead.telefono
        ).count()
        
        # Get threads with conversations but no leads
        threads_with_conversations = db.query(Thread).join(
            Conversation, Thread.id == Conversation.thread_id
        ).distinct().count()
        
        threads_with_conversations_no_leads = db.query(Thread).join(
            Conversation, Thread.id == Conversation.thread_id
        ).outerjoin(
            QualifiedLead, Thread.sender == QualifiedLead.telefono
        ).filter(
            QualifiedLead.id.is_(None)
        ).distinct().count()
        
        return {
            "success": True,
            "coverage": {
                "total_threads": total_threads,
                "threads_with_qualified_leads": threads_with_leads,
                "threads_with_conversations": threads_with_conversations,
                "threads_with_conversations_no_leads": threads_with_conversations_no_leads,
                "lead_coverage_percentage": round((threads_with_leads/total_threads*100) if total_threads > 0 else 0, 2),
                "missing_leads_from_conversations": threads_with_conversations_no_leads
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting lead coverage: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error getting lead coverage"
        }