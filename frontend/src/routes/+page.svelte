<script>
	/**
	 * Voting Page - Hauptseite für Stimmabgabe
	 * Zeigt alle Kandidaten an und ermöglicht Abstimmung
	 */

	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { getCandidates, castVote, checkVoteStatus, getClientId, WebSocketClient } from '$lib/api';
	import {
		candidates,
		setCandidates,
		hasVoted,
		setVoteStatus,
		loading,
		setError,
		showNotification
	} from '$lib/stores';

	let clientId = '';
	let selectedCandidate = null;
	let isSubmitting = false;
	let wsClient = null;
	let voteTitle = 'made with ♥ by @enl1qhtnd';

	/**
	 * Initialisierung beim Laden der Seite
	 */
	onMount(async () => {
		loading.set(true);

		try {
			// Hole Client-ID
			clientId = getClientId();

			// Prüfe Vote-Status
			const voteStatus = await checkVoteStatus(clientId);
			setVoteStatus(voteStatus.has_voted);

			// Lade Kandidaten
			const candidatesData = await getCandidates();
			setCandidates(candidatesData);

			// Lade title
			try {
				const titleResponse = await fetch(`http://${window.location.hostname}:8000/api/settings/vote-title`);
				if (titleResponse.ok) {
					const titleData = await titleResponse.json();
					voteTitle = titleData.title || 'made with ♥ by @enl1qhtnd';
				}
			} catch (e) {
				console.error('Title konnte nicht geladen werden:', e);
			}

			// WebSocket für Unlock-Event
			wsClient = new WebSocketClient();
			wsClient.on('unlock', (data) => {
				// Setze Vote-Status zurück
				setVoteStatus(false);
				// Zeige Benachrichtigung
				showNotification(data.message || 'Neue Abstimmungsrunde gestartet!', 'info');
				// Lade Seite neu (zur Homepage)
				setTimeout(() => {
					window.location.href = '/';
				}, 1500);
			});
			wsClient.connect();

		} catch (error) {
			console.error('Fehler beim Laden:', error);
			setError('Verbindung zum Server fehlgeschlagen. Bitte stelle sicher, dass der Server läuft.');
		} finally {
			loading.set(false);
		}
	});

	onDestroy(() => {
		if (wsClient) {
			wsClient.disconnect();
		}
	});

	/**
	 * Wählt einen Kandidaten aus
	 */
	function selectCandidate(candidate) {
		if ($hasVoted) return;
		selectedCandidate = candidate;
	}

	/**
	 * Gibt die Stimme ab
	 */
	async function submitVote() {
		if (!selectedCandidate || isSubmitting || $hasVoted) return;

		isSubmitting = true;

		try {
			const response = await castVote(clientId, selectedCandidate.id);

			if (response.success) {
				showNotification('Deine Stimme wurde erfolgreich registriert!', 'success');

				// Setze Vote-Status sofort für Fade-Out/In-Animation
				setVoteStatus(true, selectedCandidate.id);

				// Weiterleitung zu Ergebnissen nach 2.5 Sekunden
				setTimeout(() => {
					goto('/results');
				}, 2500);
			} else {
				setError(response.message);
			}
		} catch (error) {
			console.error('Fehler beim Abstimmen:', error);
			setError('Stimmabgabe fehlgeschlagen. Bitte versuche es erneut.');
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="min-h-screen py-8 px-4 fade-in">
	<div class="max-w-4xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-12">
			<h1 class="text-5xl font-bold text-white mb-4">easyWahl</h1>
			<p class="text-xl text-white opacity-90">{voteTitle}</p>
		</div>

		<!-- Ladezustand -->
		{#if $loading}
			<div class="text-center">
				<div class="inline-block animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white"></div>
				<p class="text-white mt-4 text-lg">Lade Kandidaten...</p>
			</div>
		{/if}

		<div class="relative min-h-[400px]">
			{#if $hasVoted}
				<!-- Bereits abgestimmt -->
				<div class="bg-white rounded-2xl shadow-2xl p-8 text-center absolute inset-0 flex flex-col items-center justify-center" in:fade={{ duration: 600, delay: 500 }}>
					<div class="text-6xl mb-4">✅</div>
					<h2 class="text-3xl font-bold text-gray-800 mb-4">Vielen Dank!</h2>
					<p class="text-lg text-gray-600 mb-6">
						Du hast bereits abgestimmt. Du kannst nur einmal pro Runde abstimmen.
					</p>
					<button
						on:click={() => goto('/results')}
						class="bg-gradient-to-r from-[#f0f2f0] to-[#000c40] text-white px-8 py-3 rounded-lg font-semibold text-lg hover:opacity-90 transition-all transform hover:scale-105"
					>
						Ergebnisse ansehen
					</button>
				</div>
			{/if}
			{#if $candidates.length === 0 && !$hasVoted && !$loading}
				<!-- Keine Kandidaten -->
				<div class="bg-white rounded-2xl shadow-2xl p-8 text-center" in:fade={{ duration: 600, delay: 500 }}>
					<div class="text-6xl mb-4">📋</div>
					<h2 class="text-2xl font-bold text-gray-800 mb-4">Keine Kandidaten verfügbar</h2>
					<p class="text-gray-600">
						Es wurden noch keine Kandidaten angelegt. Bitte wende dich an den Administrator.
					</p>
				</div>
			{/if}
			{#if !$hasVoted && $candidates.length > 0}
				<!-- Kandidaten-Auswahl -->
				<div class="bg-white rounded-2xl shadow-2xl p-8" out:fade={{ duration: 500 }}>
				<h2 class="text-3xl font-bold text-gray-800 mb-6 text-center">
					Wähle deinen Kandidaten
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 {$candidates.length % 2 !== 0 ? '[&>*:last-child]:col-span-full [&>*:last-child]:w-[calc(50%-0.5rem)] [&>*:last-child]:mx-auto' : ''}">
					{#each $candidates as candidate}
						<button
							on:click={() => selectCandidate(candidate)}
							class="candidate-card p-6 rounded-xl border-2 transition-all transform flex items-center justify-center
								{selectedCandidate?.id === candidate.id
									? 'border-sky-400 bg-sky-400 shadow-lg scale-105'
									: 'border-gray-200 hover:border-sky-300'}"
						>
							<div class="text-center">
								<h3 class="text-2xl font-bold mb-2
									{selectedCandidate?.id === candidate.id ? 'text-white' : 'text-gray-800'}">
									{candidate.name}
								</h3>
								{#if candidate.description}
									<p class="text-sm
										{selectedCandidate?.id === candidate.id ? 'text-white opacity-90' : 'text-gray-600'}">
										{candidate.description}
									</p>
								{/if}
							</div>
						</button>
					{/each}
				</div>

				<!-- Abstimmen-Button -->
				<div class="text-center">
					<button
						on:click={submitVote}
						disabled={!selectedCandidate || isSubmitting}
						class="vote-button px-12 py-4 rounded-xl font-bold text-xl text-white transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
							{selectedCandidate
								? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 shadow-lg'
								: 'bg-gray-400'}"
					>
						{#if isSubmitting}
							<span class="inline-block animate-pulse">Wird abgeschickt...</span>
						{:else if selectedCandidate}
							Jetzt abstimmen
						{:else}
							Bitte wähle einen Kandidaten
						{/if}
					</button>

					<div class="mt-6">
						<a
							href="/results"
							class="text-white hover:text-gray-200 underline transition-colors"
						>
							Zu den Ergebnissen
						</a>
					</div>
				</div>
			</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.candidate-card {
		cursor: pointer;
	}

	.vote-button {
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
	}

	.vote-button:hover:not(:disabled) {
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
	}

	.fade-in {
		animation: fadeIn 0.6s ease-in-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
