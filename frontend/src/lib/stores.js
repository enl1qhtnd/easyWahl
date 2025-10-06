/**
 * Svelte Stores für globalen State
 * Reaktive Datenverwaltung für Kandidaten, Ergebnisse und Vote-Status
 */

import { writable, derived } from 'svelte/store';

// === KANDIDATEN ===

/**
 * Store für die Kandidatenliste
 */
export const candidates = writable([]);

/**
 * Setter für Kandidaten
 */
export function setCandidates(data) {
	candidates.set(data);
}

// === VOTE STATUS ===

/**
 * Store für den Vote-Status des aktuellen Clients
 */
export const hasVoted = writable(false);

/**
 * Store für die gewählte Kandidaten-ID
 */
export const votedCandidateId = writable(null);

/**
 * Setzt den Vote-Status
 */
export function setVoteStatus(voted, candidateId = null) {
	hasVoted.set(voted);
	votedCandidateId.set(candidateId);
}

// === ERGEBNISSE ===

/**
 * Store für Abstimmungsergebnisse
 */
export const results = writable({
	results: [],
	total_votes: 0
});

/**
 * Setter für Ergebnisse
 */
export function setResults(data) {
	results.set(data);
}

// === DERIVED STORES ===

/**
 * Sortierte Ergebnisse (nach Stimmen absteigend)
 */
export const sortedResults = derived(results, ($results) => {
	return [...$results.results].sort((a, b) => b.vote_count - a.vote_count);
});

/**
 * Gewinner (Kandidat mit meisten Stimmen)
 */
export const winner = derived(sortedResults, ($sortedResults) => {
	if ($sortedResults.length === 0) return null;
	return $sortedResults[0];
});

/**
 * Berechnet Prozentsätze für alle Kandidaten
 */
export const resultsWithPercentage = derived(results, ($results) => {
	const total = $results.total_votes;

	return $results.results.map((result) => ({
		...result,
		percentage: total > 0 ? ((result.vote_count / total) * 100).toFixed(1) : 0
	}));
});

// === UI STATE ===

/**
 * Ladezustand für API-Requests
 */
export const loading = writable(false);

/**
 * Fehlermeldungen
 */
export const error = writable(null);

/**
 * Erfolgs-Benachrichtigungen
 */
export const notification = writable(null);

/**
 * Zeigt eine Benachrichtigung für 3 Sekunden
 */
export function showNotification(message, type = 'info') {
	notification.set({ message, type });

	setTimeout(() => {
		notification.set(null);
	}, 3000);
}

/**
 * Setzt eine Fehlermeldung
 */
export function setError(message) {
	error.set(message);

	setTimeout(() => {
		error.set(null);
	}, 5000);
}
