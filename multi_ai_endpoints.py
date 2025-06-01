
from flask import Blueprint, request, jsonify
import asyncio
from multi_ai_manager import MultiAIManager, CollaborativeCodeGenerator, AITask

multi_ai_bp = Blueprint('multi_ai', __name__)

@multi_ai_bp.route('/collaborate', methods=['POST'])
def collaborate():
    """Trigger multi-AI collaboration for complex tasks"""
    try:
        data = request.json
        task_type = data.get('task_type', 'code_generation')
        description = data.get('description')
        context = data.get('context', {})
        
        if not multi_ai_manager:
            return jsonify({
                "success": False,
                "error": "Multi-AI not configured. Please add API keys for additional providers."
            })
        
        # Create collaborative task
        if task_type == 'project_generation':
            result = asyncio.run(collaborative_generator.generate_enhanced_project(
                description=description,
                tech_stack=context.get('tech_stack', 'Full-Stack'),
                requirements=context.get('requirements', [])
            ))
            
            return jsonify({
                "success": True,
                "result": result,
                "collaboration_type": "project_generation"
            })
        
        elif task_type == 'code_review':
            task = AITask(
                task_type="collaborative_review",
                description=f"Review and improve this code: {description}",
                context=context
            )
            
            result = asyncio.run(multi_ai_manager.collaborative_code_generation(
                description, context.get('tech_stack', 'Unknown')
            ))
            
            return jsonify({
                "success": True,
                "result": result,
                "collaboration_type": "code_review"
            })
        
        else:
            return jsonify({
                "success": False,
                "error": f"Unknown task type: {task_type}"
            })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@multi_ai_bp.route('/ai-consensus', methods=['POST'])
def get_ai_consensus():
    """Get consensus from multiple AIs on a specific question"""
    try:
        data = request.json
        question = data.get('question')
        context = data.get('context', {})
        
        if not multi_ai_manager:
            return jsonify({
                "success": False,
                "error": "Multi-AI not configured"
            })
        
        # Create consensus task
        task = AITask(
            task_type="consensus_question",
            description=question,
            context=context
        )
        
        # Get responses from all available AIs
        responses = []
        for provider in multi_ai_manager.clients.keys():
            try:
                response = asyncio.run(multi_ai_manager._execute_primary_task(provider, task))
                responses.append({
                    "provider": provider.value,
                    "response": response.content,
                    "confidence": response.confidence,
                    "reasoning": response.reasoning
                })
            except Exception as e:
                responses.append({
                    "provider": provider.value,
                    "error": str(e)
                })
        
        # Calculate consensus
        consensus_score = sum(r.get('confidence', 0) for r in responses if 'confidence' in r) / len(responses)
        
        return jsonify({
            "success": True,
            "question": question,
            "responses": responses,
            "consensus_score": consensus_score,
            "recommendation": responses[0]['response'] if responses else "No responses available"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@multi_ai_bp.route('/ai-capabilities', methods=['GET'])
def get_ai_capabilities():
    """Get information about available AI capabilities"""
    if not multi_ai_manager:
        return jsonify({
            "success": False,
            "error": "Multi-AI not configured"
        })
    
    capabilities = {}
    for provider, specialization in multi_ai_manager.ai_specializations.items():
        if provider in multi_ai_manager.clients:
            capabilities[provider.value] = {
                "available": True,
                "strengths": specialization['strengths'],
                "best_for": specialization['use_for'],
                "status": "connected"
            }
    
    return jsonify({
        "success": True,
        "capabilities": capabilities,
        "total_ais": len(capabilities),
        "collaboration_features": [
            "Parallel code generation",
            "Cross-model code review",
            "Consensus building",
            "Specialized task assignment",
            "Quality scoring"
        ]
    })
