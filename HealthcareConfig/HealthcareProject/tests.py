
from decimal import Decimal

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .forms import MesureForm, CapteurForm
from .models import Patient, Objet, Capteur, Actionneur, Mesure, Commande


class ApplicationTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'testeur',
            password='Test-local-827!'
        )

        self.patient = Patient.objects.create(
            nomPatient='Patient Test',
            agePatient=25,
            numTelephone='5061234567',
            descriptionPatient='Patient pour les tests'
        )

        self.objet = Objet.objects.create(
            patient=self.patient,
            nom='Moniteur A',
            emplacement='Chambre A'
        )

        self.capteur = Capteur.objects.create(
            objet=self.objet,
            nom='Rythme Cardiaque A',
            type_mesure='heart',
            seuil_alerte=Decimal('120.00')
        )

        self.actionneur = Actionneur.objects.create(
            objet=self.objet,
            nom='Alerte Vocale A',
            type_action='speaker'
        )

    def connecter_api(self):
        api = APIClient()

        token = Token.objects.create(user=self.user)

        api.credentials(
            HTTP_AUTHORIZATION='Token ' + token.key
        )

        return api

    # TEST 1 : Visiteur non connecté
    def test_visiteur_redirige(self):
        self.assertEqual(
            self.client.get(reverse('tableau')).status_code,
            302
        )

        self.assertEqual(
            self.client.get('/comptes/login/').status_code,
            200
        )

    # TEST 2 : Connexion et accès aux pages
    def test_connexion_et_pages(self):
        self.assertTrue(
            self.client.login(
                username='testeur',
                password='Test-local-827!'
            )
        )

        urls = [
            reverse('tableau'),
            reverse('mesures'),
            reverse('journal'),
            reverse('liste', args=['patients']),
            reverse('liste', args=['objets']),
            reverse('liste', args=['capteurs']),
            reverse('liste', args=['actionneurs']),
            reverse('ajouter', args=['patients']),
            reverse('ajouter', args=['objets']),
            reverse('fiche', args=['patients', self.patient.pk]),
            reverse('fiche', args=['objets', self.objet.pk]),
            reverse('fiche', args=['capteurs', self.capteur.pk]),
            reverse('fiche', args=['actionneurs', self.actionneur.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    200
                )

        self.assertEqual(
            self.client.get('/HealthCare/inconnu/').status_code,
            404
        )

    # TEST 3 : Relation Patient / Objet
    def test_patient_objet(self):
        self.assertEqual(self.objet.patient, self.patient)

        self.assertIn(
            self.objet,
            self.patient.objets.all()
        )

    # TEST 4 : Plusieurs objets pour un patient
    def test_patient_plusieurs_objets(self):
        Objet.objects.create(
            patient=self.patient,
            nom='Moniteur B',
            emplacement='Chambre B'
        )

        self.assertEqual(
            self.patient.objets.count(),
            2
        )

    # TEST 5 : CRUD Patient
    def test_crud_patient(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('ajouter', args=['patients']),
            {
                'nomPatient': 'Nouveau Patient',
                'agePatient': 35,
                'numTelephone': '5069876543',
                'descriptionPatient': 'Patient de test',
            }
        )

        self.assertEqual(response.status_code, 302)

        patient = Patient.objects.get(
            nomPatient='Nouveau Patient'
        )

        self.client.post(
            reverse('modifier', args=['patients', patient.pk]),
            {
                'nomPatient': 'Patient Modifie',
                'agePatient': 36,
                'numTelephone': '5069876543',
                'descriptionPatient': 'Description modifiee',
            }
        )

        patient.refresh_from_db()

        self.assertEqual(patient.agePatient, 36)

        self.client.post(
            reverse('supprimer', args=['patients', patient.pk])
        )

        self.assertFalse(
            Patient.objects.filter(pk=patient.pk).exists()
        )

    # TEST 6 : Protection Patient
    def test_patient_protege(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse('supprimer', args=['patients', self.patient.pk])
        )

        self.assertTrue(
            Patient.objects.filter(pk=self.patient.pk).exists()
        )

    # TEST 7 : CRUD Objet
    def test_crud_objet_et_protection(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('ajouter', args=['objets']),
            {
                'patient': self.patient.pk,
                'nom': 'Moniteur B',
                'emplacement': 'Chambre B',
                'actif': 'on',
            }
        )

        self.assertEqual(response.status_code, 302)

        objet = Objet.objects.get(nom='Moniteur B')

        self.client.post(
            reverse('modifier', args=['objets', objet.pk]),
            {
                'patient': self.patient.pk,
                'nom': 'Moniteur Modifie',
                'emplacement': 'Chambre C',
                'actif': 'on',
            }
        )

        objet.refresh_from_db()

        self.assertEqual(objet.emplacement, 'Chambre C')

        self.client.get(
            reverse('supprimer', args=['objets', objet.pk])
        )

        self.assertTrue(
            Objet.objects.filter(pk=objet.pk).exists()
        )

        self.client.post(
            reverse('supprimer', args=['objets', objet.pk])
        )

        self.assertFalse(
            Objet.objects.filter(pk=objet.pk).exists()
        )

        self.client.post(
            reverse('supprimer', args=['objets', self.objet.pk])
        )

        self.assertTrue(
            Objet.objects.filter(pk=self.objet.pk).exists()
        )

    # TEST 8 : Mesure valide et invalide
    def test_mesure_valide_et_invalide(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse('mesures'),
            {
                'capteur': self.capteur.pk,
                'valeur': '130.50',
            }
        )

        self.assertEqual(
            Mesure.objects.get().valeur,
            Decimal('130.50')
        )

        self.assertContains(
            self.client.get(reverse('tableau')),
            'ALERTE'
        )

        form = MesureForm(data={
            'capteur': self.capteur.pk,
            'valeur': '700',
        })

        self.assertFalse(form.is_valid())

        self.assertEqual(Mesure.objects.count(), 1)

    # TEST 9 : Protection historique Capteur
    def test_historique_protege_type_capteur(self):
        Mesure.objects.create(
            capteur=self.capteur,
            valeur=Decimal('85.00')
        )

        form = CapteurForm(
            instance=self.capteur,
            data={
                'objet': self.objet.pk,
                'nom': 'Rythme Cardiaque A',
                'type_mesure': 'body_temp',
                'seuil_alerte': 38,
            }
        )

        self.assertFalse(form.is_valid())

    # TEST 10 : Commande et journal
    def test_commande_post_et_journal(self):
        self.client.force_login(self.user)

        url = reverse('commande', args=[self.actionneur.pk])

        self.assertEqual(
            self.client.get(url).status_code,
            405
        )

        self.client.post(url, {'etat': 'on'})

        self.actionneur.refresh_from_db()

        self.assertTrue(self.actionneur.etat)

        self.assertEqual(
            Commande.objects.get().utilisateur,
            self.user
        )

        self.client.post(url, {'etat': 'off'})

        self.actionneur.refresh_from_db()

        self.assertFalse(self.actionneur.etat)

        self.assertEqual(Commande.objects.count(), 2)

    # TEST 11 : Objet inactif
    def test_objet_inactif(self):
        self.objet.actif = False
        self.objet.save()

        self.client.force_login(self.user)

        self.client.post(
            reverse('commande', args=[self.actionneur.pk]),
            {'etat': 'on'}
        )

        self.assertEqual(Commande.objects.count(), 0)

        form = MesureForm(data={
            'capteur': self.capteur.pk,
            'valeur': '85',
        })

        self.assertFalse(form.is_valid())

    # TEST 12 : Protection CSRF
    def test_csrf_exige(self):
        client = Client(enforce_csrf_checks=True)

        client.force_login(self.user)

        response = client.post(
            reverse('commande', args=[self.actionneur.pk]),
            {'etat': 'on'}
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(Commande.objects.count(), 0)

    # TEST 13 : Patient affiché sur le tableau
    def test_tableau_patient(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('tableau'))

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            self.patient.nomPatient
        )

        self.assertEqual(
            response.context['nb_patients'],
            1
        )
