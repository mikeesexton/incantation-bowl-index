import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AgentDocsParityTests(unittest.TestCase):
    """CLAUDE.md and AGENTS.md must not drift.

    Claude Code reads one and Codex reads the other. When they disagree the two
    agents work to different rules and nobody notices until the corpus does.
    """
    def body(self, name):
        lines = (ROOT / name).read_text(encoding='utf-8').splitlines(keepends=True)
        self.assertTrue(lines, '%s is empty' % name)
        self.assertTrue(lines[0].startswith('# '), '%s must open with a title line' % name)
        return ''.join(lines[1:])
    def test_bodies_are_identical_below_the_title(self):
        self.assertEqual(
            self.body('CLAUDE.md'), self.body('AGENTS.md'),
            'CLAUDE.md and AGENTS.md have drifted. Change docs/project-rules.md, '
            'then copy the shared body into both files.',
        )
    def test_titles_name_their_agent(self):
        self.assertIn('Claude', (ROOT / 'CLAUDE.md').read_text(encoding='utf-8').splitlines()[0])
        self.assertIn('Codex', (ROOT / 'AGENTS.md').read_text(encoding='utf-8').splitlines()[0])
    def test_both_point_at_the_single_source_of_truth(self):
        for name in ('CLAUDE.md', 'AGENTS.md'):
            self.assertIn('docs/project-rules.md', (ROOT / name).read_text(encoding='utf-8'))
    def test_referenced_project_documents_exist(self):
        for relative in (
            'docs/project-rules.md', 'docs/research_protocol.md',
            'docs/conflict_review_workflow.md', 'docs/evidence_review_and_release.md',
            'docs/dataset_maturity_roadmap.md', 'research/literature/README.md',
            'research/roadmap/dataset_maturity.json', 'task-log.md',
            'docs/licensing.md', 'LICENSE', 'LICENSE-DATA',
        ):
            self.assertTrue((ROOT / relative).exists(), '%s is referenced but missing' % relative)

if __name__ == '__main__':
    unittest.main()
