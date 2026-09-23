import unittest

from app.seed import SYNTHETIC_CARDS, SYNTHETIC_DRAFTS, SYNTHETIC_PROPOSALS, SYNTHETIC_TEAMS


class SyntheticDataTests(unittest.TestCase):
    def test_minimum_demo_dataset_is_present(self) -> None:
        self.assertGreaterEqual(len(SYNTHETIC_DRAFTS), 5)
        self.assertGreaterEqual(len(SYNTHETIC_CARDS), 5)
        self.assertGreaterEqual(len(SYNTHETIC_TEAMS), 5)
        self.assertGreaterEqual(len(SYNTHETIC_PROPOSALS), 5)

    def test_identifiers_and_relations_are_valid(self) -> None:
        card_ids = {card["id"] for card in SYNTHETIC_CARDS}
        draft_ids = {draft["id"] for draft in SYNTHETIC_DRAFTS}
        team_ids = {team["id"] for team in SYNTHETIC_TEAMS}

        self.assertEqual(len(card_ids), len(SYNTHETIC_CARDS))
        self.assertEqual(len(draft_ids), len(SYNTHETIC_DRAFTS))
        self.assertEqual(len(team_ids), len(SYNTHETIC_TEAMS))
        self.assertTrue(all(card["draft_id"] in draft_ids for card in SYNTHETIC_CARDS))
        self.assertTrue(all(proposal["task_id"] in card_ids for proposal in SYNTHETIC_PROPOSALS))
        self.assertTrue(all(proposal["team_id"] in team_ids for proposal in SYNTHETIC_PROPOSALS))

    def test_examples_cover_all_readiness_levels(self) -> None:
        self.assertEqual({card["score_level"] for card in SYNTHETIC_CARDS}, {"draft", "workable", "ready", "priority"})

    def test_stored_totals_match_criterion_breakdowns(self) -> None:
        for card in SYNTHETIC_CARDS:
            earned = sum(item["earned"] for item in card["score"]["criteria"].values())
            self.assertEqual(card["score_total"], earned)
            self.assertEqual(card["score"]["total"], earned)
            self.assertEqual(card["score_level"], card["score"]["level"])

    def test_every_draft_has_at_least_three_contextual_questions(self) -> None:
        self.assertTrue(all(len(draft["questions"]) >= 3 for draft in SYNTHETIC_DRAFTS))

    def test_contacts_and_links_are_synthetic(self) -> None:
        contacts = [team["contact"] for team in SYNTHETIC_TEAMS]
        contacts.extend(card["contact"] for card in SYNTHETIC_CARDS if card["contact"])
        links = [proposal["prototype_url"] for proposal in SYNTHETIC_PROPOSALS]

        self.assertTrue(all(value.endswith(".test") for value in contacts))
        self.assertTrue(all("example.test" in value for value in links))


if __name__ == "__main__":
    unittest.main()
