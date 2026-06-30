import unittest
from competitive_intelligence_agent.pipeline import graph

class GraphInterruptTests(unittest.TestCase):
    def test_graph_interrupts_and_resumes(self):
        if graph is None:
            self.skipTest("LangGraph is not installed or import failed")

        config = {"configurable": {"thread_id": "test-thread-1"}}
        initial_state = {"competitor_name": "HubSpot"}

        # Run until the interrupt point
        events = []
        for event in graph.stream(initial_state, config):
            events.append(event)

        # Get current state
        state = graph.get_state(config)
        
        # Verify it paused after hypothesis and before recommendation
        self.assertIn("hypotheses", state.values)
        self.assertNotIn("recommendations", state.values)
        self.assertEqual(state.next, ("recommendation",))

        # Resume execution by streaming with None
        resume_events = []
        for event in graph.stream(None, config):
            resume_events.append(event)

        # Verify state after resume
        final_state = graph.get_state(config)
        self.assertIn("recommendations", final_state.values)
        self.assertEqual(final_state.next, ())

if __name__ == "__main__":
    unittest.main()
