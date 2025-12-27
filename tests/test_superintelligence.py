"""Tests for Superintelligence Module"""

import pytest
import numpy as np
from src.superintelligence import (
    Knowledge,
    ReasoningEngine,
    SelfImprovementEngine,
    GoalPlanner,
    Superintelligence
)


class TestKnowledge:
    """Test Knowledge dataclass"""
    
    def test_knowledge_creation(self):
        knowledge = Knowledge(
            domain="test_domain",
            facts=["fact1", "fact2"],
            confidence=0.9,
            timestamp=1.0
        )
        assert knowledge.domain == "test_domain"
        assert len(knowledge.facts) == 2
        assert knowledge.confidence == 0.9
        assert knowledge.timestamp == 1.0


class TestReasoningEngine:
    """Test ReasoningEngine"""
    
    def test_engine_initialization(self):
        engine = ReasoningEngine()
        assert len(engine.knowledge_base) == 0
        assert engine.reasoning_depth == 10
        
    def test_add_knowledge(self):
        engine = ReasoningEngine()
        engine.add_knowledge("physics", ["gravity exists", "light travels"], 0.95)
        assert len(engine.knowledge_base) == 1
        assert engine.knowledge_base[0].domain == "physics"
        
    def test_infer_basic(self):
        engine = ReasoningEngine()
        premises = ["A implies B", "B implies C"]
        conclusions = engine.infer(premises)
        assert isinstance(conclusions, list)
        
    def test_reason_about(self):
        engine = ReasoningEngine()
        engine.add_knowledge("ai", ["neural networks learn"], 0.9)
        result = engine.reason_about("ai models")
        assert "query" in result
        assert "confidence" in result
        assert isinstance(result["steps"], list)


class TestSelfImprovementEngine:
    """Test SelfImprovementEngine"""
    
    def test_engine_initialization(self):
        engine = SelfImprovementEngine()
        assert len(engine.performance_history) == 0
        assert engine.improvement_rate == 0.01
        assert len(engine.capabilities) == 5
        
    def test_improve(self):
        engine = SelfImprovementEngine()
        initial_reasoning = engine.capabilities["reasoning"]
        feedback = {"reasoning": 0.8, "learning": 0.9}
        engine.improve(feedback)
        assert len(engine.performance_history) == 1
        
    def test_get_capability_score(self):
        engine = SelfImprovementEngine()
        score = engine.get_capability_score()
        assert isinstance(score, float)
        assert score >= 0.0
        
    def test_identify_weaknesses(self):
        engine = SelfImprovementEngine()
        weaknesses = engine.identify_weaknesses()
        assert isinstance(weaknesses, list)


class TestGoalPlanner:
    """Test GoalPlanner"""
    
    def test_planner_initialization(self):
        planner = GoalPlanner()
        assert len(planner.goals) == 0
        assert len(planner.completed_goals) == 0
        
    def test_create_goal(self):
        planner = GoalPlanner()
        goal = planner.create_goal("Test goal", priority=8)
        assert goal["description"] == "Test goal"
        assert goal["priority"] == 8
        assert goal["status"] == "planned"
        assert len(planner.goals) == 1
        
    def test_decompose_goal(self):
        planner = GoalPlanner()
        goal = planner.create_goal("Main goal")
        subgoals = planner.decompose_goal(goal, num_subgoals=3)
        assert len(subgoals) == 3
        assert len(goal["subgoals"]) == 3
        
    def test_execute_goal(self):
        planner = GoalPlanner()
        goal = planner.create_goal("Task to complete")
        goal_id = goal["id"]
        planner.execute_goal(goal_id, progress=1.0)
        assert len(planner.completed_goals) == 1
        assert len(planner.goals) == 0
        
    def test_get_next_goal(self):
        planner = GoalPlanner()
        planner.create_goal("Low priority", priority=3)
        planner.create_goal("High priority", priority=10)
        next_goal = planner.get_next_goal()
        assert next_goal["priority"] == 10


class TestSuperintelligence:
    """Test Superintelligence"""
    
    def test_si_initialization(self):
        si = Superintelligence()
        assert isinstance(si.reasoning_engine, ReasoningEngine)
        assert isinstance(si.improvement_engine, SelfImprovementEngine)
        assert isinstance(si.goal_planner, GoalPlanner)
        assert si.consciousness_level == 1.0
        
    def test_think(self):
        si = Superintelligence()
        result = si.think("solve optimization problem")
        assert "problem" in result
        assert "reasoning" in result
        assert "plan" in result
        assert "capability_score" in result
        
    def test_learn(self):
        si = Superintelligence()
        initial_consciousness = si.consciousness_level
        experience = {
            "domain": "mathematics",
            "facts": ["2+2=4", "pi is irrational"],
            "confidence": 0.95,
            "performance": {"reasoning": 0.85}
        }
        si.learn(experience)
        assert si.consciousness_level >= initial_consciousness
        assert len(si.reasoning_engine.knowledge_base) == 1
        
    def test_autonomous_decision(self):
        si = Superintelligence()
        context = {
            "options": ["option_a", "option_b", "option_c"],
            "constraints": ["time", "budget"]
        }
        decision = si.autonomous_decision(context)
        assert decision in context["options"] or decision == "No action"
