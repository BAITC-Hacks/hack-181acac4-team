import unittest
from uuid import uuid4

from sqlalchemy.orm import Session

from app import models
import test_intake


class IntegrationTests(unittest.TestCase):
    setUp = test_intake.IntakeFlowTests.setUp
    tearDown = test_intake.IntakeFlowTests.tearDown
    create_card = test_intake.IntakeFlowTests.create_card

    def test_complete_flow_with_multiple_independent_proposals(self):
        _, card, _ = self.create_card()
        card_id = card['id']
        route = f'/api/cards/{card_id}'
        self.assertEqual(self.client.get('/api/tasks').json(), [])
        first = self.client.post(f'{route}/confirm').json()
        self.assertEqual(first['score']['total'], 35)
        self.client.post(f'{route}/publish')
        self.assertEqual(self.client.get('/api/tasks?level=draft').json()[0]['id'], card_id)

        team_ids = [uuid4(), uuid4()]
        with Session(self.engine) as db:
            for index, team_id in enumerate(team_ids):
                db.add(models.TeamProfile(id=team_id, name=f'Team {index}', skills=[], interests=[], contact='demo@example.test'))
            db.commit()
        self.assertEqual(len(self.client.get('/api/teams').json()), 2)
        proposal_ids = []
        for team_id in [*team_ids, team_ids[0]]:
            response = self.client.post(f'/api/tasks/{card_id}/proposals', json={
                'team_id': str(team_id), 'idea': 'Бот заказов', 'plan': 'Прототип и проверка',
                'timeline': 'Две недели', 'prototype_url': 'https://example.test/demo',
            })
            self.assertEqual(response.status_code, 201, response.text)
            proposal_ids.append(response.json()['id'])
        for proposal_id in proposal_ids[:2]:
            self.assertEqual(self.client.post(f'/api/proposals/{proposal_id}/decision', json={'decision': 'accepted'}).status_code, 200)
        statuses = {p['id']: p['status'] for p in self.client.get(f'/api/tasks/{card_id}/proposals').json()}
        self.assertEqual([statuses[p] for p in proposal_ids], ['accepted', 'accepted', 'submitted'])
        self.client.post(f'/api/proposals/{proposal_ids[2]}/decision', json={'decision': 'rejected'})

        self.client.patch(route, json={
            'title': 'Учёт заказов', 'topic': 'Cafe', 'need': 'Не терять заказы',
            'data': 'CSV заказов', 'expected_result': 'Рабочий бот', 'constraints': 'Две недели',
            'contact': 'demo@example.test', 'interaction_format': 'Созвон',
        })
        self.assertEqual(self.client.get('/api/tasks').json(), [])
        self.assertEqual(self.client.post(f'{route}/publish').status_code, 409)
        self.assertEqual(self.client.post(f'{route}/confirm').json()['score']['total'], 100)
        self.client.post(f'{route}/publish')
        self.assertEqual(len(self.client.get('/api/tasks?topic=cafe&level=priority').json()), 1)
        self.assertEqual(self.client.get('/api/tasks?level=draft').json(), [])
        self.assertEqual(len(self.client.get(f'/api/tasks/{card_id}/proposals').json()), 3)

    def test_proposal_validation_and_unpublished_visibility(self):
        _, card, _ = self.create_card()
        route = f"/api/tasks/{card['id']}"
        self.assertEqual(self.client.get(route).status_code, 404)
        payload = {'team_id': str(uuid4()), 'idea': 'Идея', 'plan': 'План', 'timeline': 'Неделя'}
        self.assertEqual(self.client.post(f'{route}/proposals', json=payload).status_code, 404)
        self.client.post(f"/api/cards/{card['id']}/confirm")
        self.client.post(f"/api/cards/{card['id']}/publish")
        self.assertEqual(self.client.post(f'{route}/proposals', json=payload).status_code, 404)
        for field in ['idea', 'plan', 'timeline']:
            invalid = {**payload, field: '   '}
            self.assertEqual(self.client.post(f'{route}/proposals', json=invalid).status_code, 422)
        self.assertEqual(self.client.post(f'/api/proposals/{uuid4()}/decision', json={'decision': 'automatic'}).status_code, 422)
