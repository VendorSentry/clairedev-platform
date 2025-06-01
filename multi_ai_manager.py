
import openai
import anthropic
import google.generativeai as genai
from mistralai.client import MistralClient
from typing import Dict, List, Optional, Any
import asyncio
import json
import time
from dataclasses import dataclass
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"

@dataclass
class AIResponse:
    provider: AIProvider
    content: str
    confidence: float
    reasoning: str
    execution_time: float
    tokens_used: int

@dataclass
class AITask:
    task_type: str
    description: str
    context: Dict[str, Any]
    priority: int = 1

class MultiAIManager:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.clients = self._initialize_clients()
        self.ai_specializations = self._define_specializations()
        
    def _initialize_clients(self):
        clients = {}
        
        if self.api_keys.get('openai'):
            clients[AIProvider.OPENAI] = openai.OpenAI(api_key=self.api_keys['openai'])
            
        if self.api_keys.get('anthropic'):
            clients[AIProvider.ANTHROPIC] = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            
        if self.api_keys.get('gemini'):
            genai.configure(api_key=self.api_keys['gemini'])
            clients[AIProvider.GEMINI] = genai.GenerativeModel('gemini-pro')
            
        if self.api_keys.get('mistral'):
            clients[AIProvider.MISTRAL] = MistralClient(api_key=self.api_keys['mistral'])
            
        return clients
    
    def _define_specializations(self):
        """Define what each AI is best at"""
        return {
            AIProvider.OPENAI: {
                'strengths': ['code_generation', 'project_architecture', 'debugging', 'documentation'],
                'use_for': ['complex_coding', 'system_design', 'api_development']
            },
            AIProvider.ANTHROPIC: {
                'strengths': ['code_analysis', 'security_review', 'best_practices', 'refactoring'],
                'use_for': ['code_review', 'optimization', 'safety_checks']
            },
            AIProvider.GEMINI: {
                'strengths': ['ui_design', 'frontend_development', 'user_experience', 'creative_solutions'],
                'use_for': ['frontend_code', 'design_patterns', 'user_interfaces']
            },
            AIProvider.MISTRAL: {
                'strengths': ['performance_optimization', 'algorithms', 'data_structures', 'efficiency'],
                'use_for': ['performance_tuning', 'algorithm_design', 'backend_optimization']
            }
        }
    
    async def collaborative_code_generation(self, project_description: str, tech_stack: str) -> Dict[str, Any]:
        """Generate code using multiple AIs collaboratively"""
        
        # Phase 1: Architecture Design (OpenAI leads)
        architecture_task = AITask(
            task_type="architecture_design",
            description=f"Design system architecture for: {project_description}",
            context={"tech_stack": tech_stack, "project_description": project_description}
        )
        
        architecture = await self._execute_primary_task(AIProvider.OPENAI, architecture_task)
        
        # Phase 2: Parallel code generation
        tasks = [
            AITask("frontend_code", "Generate frontend components", {"architecture": architecture.content}),
            AITask("backend_code", "Generate backend services", {"architecture": architecture.content}),
            AITask("database_design", "Design database schema", {"architecture": architecture.content}),
            AITask("api_design", "Design API endpoints", {"architecture": architecture.content})
        ]
        
        responses = await self._execute_parallel_tasks(tasks)
        
        # Phase 3: Code review and optimization
        combined_code = self._combine_responses(responses)
        review_tasks = [
            AITask("security_review", "Review code for security issues", {"code": combined_code}),
            AITask("performance_review", "Optimize for performance", {"code": combined_code}),
            AITask("best_practices_review", "Apply best practices", {"code": combined_code})
        ]
        
        reviews = await self._execute_review_tasks(review_tasks)
        
        # Phase 4: Final integration and consensus
        final_code = await self._reach_consensus(combined_code, reviews)
        
        return {
            "architecture": architecture.content,
            "code": final_code,
            "reviews": reviews,
            "collaboration_summary": self._generate_collaboration_summary(responses, reviews)
        }
    
    async def _execute_primary_task(self, provider: AIProvider, task: AITask) -> AIResponse:
        """Execute a primary task with a specific AI"""
        if provider not in self.clients:
            raise ValueError(f"Provider {provider} not available")
        
        start_time = time.time()
        
        if provider == AIProvider.OPENAI:
            response = await self._query_openai(task)
        elif provider == AIProvider.ANTHROPIC:
            response = await self._query_anthropic(task)
        elif provider == AIProvider.GEMINI:
            response = await self._query_gemini(task)
        elif provider == AIProvider.MISTRAL:
            response = await self._query_mistral(task)
        
        execution_time = time.time() - start_time
        
        return AIResponse(
            provider=provider,
            content=response['content'],
            confidence=response.get('confidence', 0.8),
            reasoning=response.get('reasoning', ''),
            execution_time=execution_time,
            tokens_used=response.get('tokens_used', 0)
        )
    
    async def _execute_parallel_tasks(self, tasks: List[AITask]) -> List[AIResponse]:
        """Execute multiple tasks in parallel using best-suited AIs"""
        task_assignments = []
        
        for task in tasks:
            best_provider = self._select_best_provider(task)
            task_assignments.append((best_provider, task))
        
        # Execute all tasks concurrently
        responses = await asyncio.gather(*[
            self._execute_primary_task(provider, task) 
            for provider, task in task_assignments
        ])
        
        return responses
    
    def _select_best_provider(self, task: AITask) -> AIProvider:
        """Select the best AI provider for a specific task"""
        task_type = task.task_type
        
        provider_scores = {}
        for provider, spec in self.ai_specializations.items():
            if provider not in self.clients:
                continue
                
            score = 0
            if any(strength in task_type for strength in spec['strengths']):
                score += 3
            if any(use_case in task_type for use_case in spec['use_for']):
                score += 2
                
            provider_scores[provider] = score
        
        if not provider_scores:
            return list(self.clients.keys())[0]  # Fallback to first available
            
        return max(provider_scores.items(), key=lambda x: x[1])[0]
    
    async def _execute_review_tasks(self, tasks: List[AITask]) -> List[AIResponse]:
        """Execute review tasks with specialized AIs"""
        reviews = []
        
        for task in tasks:
            if "security" in task.task_type and AIProvider.ANTHROPIC in self.clients:
                provider = AIProvider.ANTHROPIC
            elif "performance" in task.task_type and AIProvider.MISTRAL in self.clients:
                provider = AIProvider.MISTRAL
            else:
                provider = self._select_best_provider(task)
            
            review = await self._execute_primary_task(provider, task)
            reviews.append(review)
        
        return reviews
    
    async def _reach_consensus(self, code: str, reviews: List[AIResponse]) -> str:
        """Have AIs reach consensus on final code"""
        consensus_task = AITask(
            "consensus_building",
            "Integrate feedback and create final optimized code",
            {
                "original_code": code,
                "reviews": [r.content for r in reviews],
                "feedback_summary": self._summarize_reviews(reviews)
            }
        )
        
        # Use the most capable AI for final integration
        best_provider = AIProvider.OPENAI if AIProvider.OPENAI in self.clients else list(self.clients.keys())[0]
        final_response = await self._execute_primary_task(best_provider, consensus_task)
        
        return final_response.content
    
    async def _query_openai(self, task: AITask) -> Dict[str, Any]:
        """Query OpenAI with enhanced prompts"""
        system_prompt = f"""You are an expert software architect collaborating with other AI systems. 
        Task: {task.task_type}
        Focus on: {self.ai_specializations[AIProvider.OPENAI]['strengths']}
        
        Provide your response in JSON format with:
        - content: Your main response
        - confidence: Your confidence level (0-1)
        - reasoning: Why you chose this approach
        """
        
        response = await self.clients[AIProvider.OPENAI].chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{task.description}\n\nContext: {json.dumps(task.context)}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            result['tokens_used'] = response.usage.total_tokens
            return result
        except:
            return {
                "content": response.choices[0].message.content,
                "confidence": 0.8,
                "reasoning": "Standard response",
                "tokens_used": response.usage.total_tokens
            }
    
    async def _query_anthropic(self, task: AITask) -> Dict[str, Any]:
        """Query Anthropic Claude"""
        prompt = f"""Task: {task.task_type}
        Description: {task.description}
        Context: {json.dumps(task.context)}
        
        As an AI specializing in {self.ai_specializations[AIProvider.ANTHROPIC]['strengths']}, 
        provide your analysis and recommendations.
        
        Respond in JSON format with content, confidence, and reasoning.
        """
        
        message = await self.clients[AIProvider.ANTHROPIC].messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(message.content[0].text)
            result['tokens_used'] = message.usage.input_tokens + message.usage.output_tokens
            return result
        except:
            return {
                "content": message.content[0].text,
                "confidence": 0.8,
                "reasoning": "Standard response",
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens
            }
    
    async def _query_gemini(self, task: AITask) -> Dict[str, Any]:
        """Query Google Gemini"""
        prompt = f"""Task: {task.task_type}
        Description: {task.description}
        Context: {json.dumps(task.context)}
        
        Focus on: {self.ai_specializations[AIProvider.GEMINI]['strengths']}
        
        Provide response in JSON format with content, confidence, and reasoning.
        """
        
        response = await self.clients[AIProvider.GEMINI].generate_content_async(prompt)
        
        try:
            result = json.loads(response.text)
            result['tokens_used'] = len(response.text.split())  # Approximation
            return result
        except:
            return {
                "content": response.text,
                "confidence": 0.8,
                "reasoning": "Standard response",
                "tokens_used": len(response.text.split())
            }
    
    async def _query_mistral(self, task: AITask) -> Dict[str, Any]:
        """Query Mistral AI"""
        prompt = f"""Task: {task.task_type}
        Description: {task.description}
        Context: {json.dumps(task.context)}
        
        Specializing in: {self.ai_specializations[AIProvider.MISTRAL]['strengths']}
        
        Respond in JSON with content, confidence, and reasoning.
        """
        
        response = await self.clients[AIProvider.MISTRAL].chat(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            result['tokens_used'] = response.usage.total_tokens
            return result
        except:
            return {
                "content": response.choices[0].message.content,
                "confidence": 0.8,
                "reasoning": "Standard response",
                "tokens_used": response.usage.total_tokens
            }
    
    def _combine_responses(self, responses: List[AIResponse]) -> str:
        """Combine multiple AI responses into cohesive code"""
        combined = "// === MULTI-AI COLLABORATIVE CODE ===\n\n"
        
        for i, response in enumerate(responses, 1):
            combined += f"// === Section {i}: Generated by {response.provider.value} ===\n"
            combined += f"// Confidence: {response.confidence}, Execution Time: {response.execution_time:.2f}s\n"
            combined += response.content + "\n\n"
        
        return combined
    
    def _summarize_reviews(self, reviews: List[AIResponse]) -> str:
        """Summarize all review feedback"""
        summary = "Review Summary:\n"
        for review in reviews:
            summary += f"- {review.provider.value}: {review.content[:200]}...\n"
        return summary
    
    def _generate_collaboration_summary(self, responses: List[AIResponse], reviews: List[AIResponse]) -> Dict[str, Any]:
        """Generate a summary of the collaboration process"""
        return {
            "total_ais_used": len(set(r.provider for r in responses + reviews)),
            "total_execution_time": sum(r.execution_time for r in responses + reviews),
            "average_confidence": sum(r.confidence for r in responses + reviews) / len(responses + reviews),
            "total_tokens_used": sum(r.tokens_used for r in responses + reviews),
            "providers_used": [r.provider.value for r in responses + reviews],
            "specializations_applied": [
                f"{r.provider.value}: {self.ai_specializations[r.provider]['strengths']}" 
                for r in responses + reviews
            ]
        }

class CollaborativeCodeGenerator:
    def __init__(self, multi_ai_manager: MultiAIManager):
        self.ai_manager = multi_ai_manager
    
    async def generate_enhanced_project(self, description: str, tech_stack: str, requirements: List[str] = None) -> Dict[str, Any]:
        """Generate a project using collaborative AI approach"""
        
        # Enhanced project generation with multi-AI collaboration
        result = await self.ai_manager.collaborative_code_generation(description, tech_stack)
        
        # Extract files from the collaborative result
        files = self._extract_files_from_collaborative_result(result)
        
        # Generate additional project assets
        additional_assets = await self._generate_project_assets(description, tech_stack, files)
        
        return {
            "repo_name": self._generate_repo_name(description),
            "description": description,
            "tech_stack": tech_stack,
            "files": {**files, **additional_assets},
            "collaboration_summary": result["collaboration_summary"],
            "ai_insights": self._generate_ai_insights(result),
            "quality_score": self._calculate_quality_score(result)
        }
    
    def _extract_files_from_collaborative_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Extract individual files from collaborative AI result"""
        # This would parse the collaborative code and split it into files
        # Implementation depends on how the AIs structure their responses
        
        files = {}
        code_content = result.get("code", "")
        
        # Simple file extraction logic (can be enhanced)
        current_file = None
        current_content = []
        
        for line in code_content.split('\n'):
            if line.startswith('// FILE:') or line.startswith('# FILE:'):
                if current_file:
                    files[current_file] = '\n'.join(current_content)
                current_file = line.split(':', 1)[1].strip()
                current_content = []
            elif current_file:
                current_content.append(line)
        
        if current_file:
            files[current_file] = '\n'.join(current_content)
        
        return files if files else {"main.py": code_content}
    
    async def _generate_project_assets(self, description: str, tech_stack: str, files: Dict[str, str]) -> Dict[str, str]:
        """Generate additional project assets like README, tests, etc."""
        assets = {}
        
        # Generate README
        readme_task = AITask(
            "documentation",
            f"Generate comprehensive README for {description}",
            {"tech_stack": tech_stack, "files": list(files.keys())}
        )
        
        # Generate deployment configuration
        deploy_task = AITask(
            "deployment_config",
            f"Generate deployment configuration for {tech_stack}",
            {"project_files": files}
        )
        
        # Use the best available AI for documentation
        if AIProvider.ANTHROPIC in self.ai_manager.clients:
            readme_response = await self.ai_manager._execute_primary_task(AIProvider.ANTHROPIC, readme_task)
            assets["README.md"] = readme_response.content
        
        if AIProvider.MISTRAL in self.ai_manager.clients:
            deploy_response = await self.ai_manager._execute_primary_task(AIProvider.MISTRAL, deploy_task)
            assets["deploy.yml"] = deploy_response.content
        
        return assets
    
    def _generate_repo_name(self, description: str) -> str:
        """Generate a suitable repository name"""
        import re
        # Simple repo name generation
        name = re.sub(r'[^a-zA-Z0-9\s]', '', description.lower())
        name = re.sub(r'\s+', '-', name.strip())
        return name[:50] if len(name) > 50 else name
    
    def _generate_ai_insights(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights about the AI collaboration"""
        return {
            "architecture_quality": "High" if "microservice" in result.get("architecture", "").lower() else "Standard",
            "code_complexity": len(result.get("code", "")),
            "review_findings": len(result.get("reviews", [])),
            "collaboration_efficiency": result["collaboration_summary"]["average_confidence"]
        }
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate overall quality score based on AI collaboration"""
        base_score = result["collaboration_summary"]["average_confidence"]
        
        # Bonus for multiple AIs
        ai_bonus = min(0.1 * result["collaboration_summary"]["total_ais_used"], 0.3)
        
        # Bonus for reviews
        review_bonus = min(0.05 * len(result.get("reviews", [])), 0.2)
        
        return min(base_score + ai_bonus + review_bonus, 1.0)

class MultiAIManager:
    def __init__(self):
        self.providers = {}
    
    def collaborate(self, task: str):
        """Coordinate multiple AI providers"""
        return {"success": True, "result": f"Completed: {task}"}
class MultiAIManager:
    """Basic multi-AI manager - handles multiple AI providers"""
    
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.available_providers = []
        
        if api_keys.get('openai'):
            self.available_providers.append('openai')
        if api_keys.get('anthropic'):
            self.available_providers.append('anthropic')
    
    def generate_code(self, prompt, provider='openai'):
        """Generate code using specified provider"""
        if provider not in self.available_providers:
            return {"error": f"Provider {provider} not available"}
        
        return {"code": "# Generated code placeholder", "provider": provider}
    
    def get_available_providers(self):
        """Get list of available AI providers"""
        return self.available_providers
