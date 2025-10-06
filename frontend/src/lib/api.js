/**
 * API Client für Backend-Kommunikation
 * Alle REST-Endpoints und WebSocket-Verbindung
 */

// Dynamische Hostname-Erkennung für LAN/Remote-Zugriff
const getHostname = () => {
	if (typeof window !== 'undefined') {
		return window.location.hostname;
	}
	return 'localhost'; // Fallback für Server-Side Rendering
};

const API_BASE = `http://${getHostname()}:8000`;
const WS_BASE = `ws://${getHostname()}:8000`;

/**
 * Generischer Fetch-Wrapper mit Error-Handling
 */
async function apiRequest(endpoint, options = {}) {
	try {
		const response = await fetch(`${API_BASE}${endpoint}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			}
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.status}`);
		}

		return await response.json();
	} catch (error) {
		console.error('API Request failed:', error);
		throw error;
	}
}

// === KANDIDATEN ===

/**
 * Lädt alle Kandidaten
 */
export async function getCandidates() {
	return apiRequest('/api/candidates');
}

// === VOTING ===

/**
 * Gibt eine Stimme ab
 */
export async function castVote(clientId, candidateId) {
	return apiRequest('/api/vote', {
		method: 'POST',
		body: JSON.stringify({
			candidate_id: candidateId
		})
	});
}

/**
 * Prüft ob Client bereits abgestimmt hat
 */
export async function checkVoteStatus() {
	return apiRequest('/api/vote/check', {
		method: 'POST',
		body: JSON.stringify({})
	});
}

// === ERGEBNISSE ===

/**
 * Lädt aktuelle Abstimmungsergebnisse
 */
export async function getResults() {
	return apiRequest('/api/results');
}

// === CLIENT-ID VERWALTUNG ===

/**
 * Generiert oder lädt Client-ID aus localStorage
 * Kombiniert mit Browser-Fingerprint für zusätzliche Sicherheit
 */
export function getClientId() {
	const STORAGE_KEY = 'easywahl_client_id';

	// Versuche existierende ID zu laden
	let clientId = localStorage.getItem(STORAGE_KEY);

	if (!clientId) {
		// Generiere neue ID aus Timestamp + Random + Browser-Fingerprint
		const timestamp = Date.now();
		const random = Math.random().toString(36).substring(2, 15);
		const fingerprint = getBrowserFingerprint();

		clientId = `${timestamp}-${random}-${fingerprint}`;
		localStorage.setItem(STORAGE_KEY, clientId);
	}

	return clientId;
}

/**
 * Einfacher Browser-Fingerprint
 * (userAgent + screen + timezone)
 */
function getBrowserFingerprint() {
	const ua = navigator.userAgent;
	const screen = `${window.screen.width}x${window.screen.height}`;
	const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;

	const fingerprint = `${ua}-${screen}-${tz}`;

	// Einfacher Hash
	let hash = 0;
	for (let i = 0; i < fingerprint.length; i++) {
		const char = fingerprint.charCodeAt(i);
		hash = (hash << 5) - hash + char;
		hash = hash & hash; // Convert to 32bit integer
	}

	return Math.abs(hash).toString(36);
}

// === WEBSOCKET ===

/**
 * WebSocket-Manager für Live-Updates
 */
export class WebSocketClient {
	constructor() {
		this.ws = null;
		this.reconnectInterval = 5000;
		this.listeners = new Map();
	}

	/**
	 * Verbindet zum WebSocket-Server
	 */
	connect() {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			return;
		}

		try {
			this.ws = new WebSocket(`${WS_BASE}/ws`);

			this.ws.onopen = () => {
				console.log('WebSocket verbunden');
			};

			this.ws.onmessage = (event) => {
				try {
					const message = JSON.parse(event.data);
					this.handleMessage(message);
				} catch (error) {
					console.error('WebSocket message parse error:', error);
				}
			};

			this.ws.onerror = (error) => {
				console.error('WebSocket error:', error);
			};

			this.ws.onclose = () => {
				console.log('WebSocket getrennt, reconnect in 5s...');
				setTimeout(() => this.connect(), this.reconnectInterval);
			};
		} catch (error) {
			console.error('WebSocket connection failed:', error);
			setTimeout(() => this.connect(), this.reconnectInterval);
		}
	}

	/**
	 * Verarbeitet eingehende WebSocket-Nachrichten
	 */
	handleMessage(message) {
		const { type, data } = message;

		// Rufe registrierte Listener auf
		if (this.listeners.has(type)) {
			this.listeners.get(type).forEach((callback) => {
				callback(data);
			});
		}

		// Rufe allgemeine Listener auf
		if (this.listeners.has('*')) {
			this.listeners.get('*').forEach((callback) => {
				callback(message);
			});
		}
	}

	/**
	 * Registriert einen Listener für einen Message-Type
	 * @param {string} type - Message-Type oder '*' für alle
	 * @param {function} callback - Callback-Funktion
	 */
	on(type, callback) {
		if (!this.listeners.has(type)) {
			this.listeners.set(type, []);
		}
		this.listeners.get(type).push(callback);
	}

	/**
	 * Entfernt einen Listener
	 */
	off(type, callback) {
		if (this.listeners.has(type)) {
			const callbacks = this.listeners.get(type);
			const index = callbacks.indexOf(callback);
			if (index > -1) {
				callbacks.splice(index, 1);
			}
		}
	}

	/**
	 * Trennt die WebSocket-Verbindung
	 */
	disconnect() {
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
	}
}
