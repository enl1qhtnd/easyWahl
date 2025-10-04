<script>
	/**
	 * Results Page - Live-Ergebnisanzeige
	 * Zeigt Abstimmungsergebnisse in Echtzeit via WebSocket
	 */

	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { getResults, WebSocketClient } from '$lib/api';
	import {
		results,
		setResults,
		resultsWithPercentage,
		loading,
		setError,
		showNotification
	} from '$lib/stores';

	let wsClient = null;
	let chartCanvas;
	let chartInstance = null;
	let Chart = null;

	/**
	 * Initialisierung beim Laden
	 */
	onMount(async () => {
		loading.set(true);

		try {
			// Dynamischer Import von Chart.js (nur im Browser)
			const chartModule = await import('chart.js');
			Chart = chartModule.Chart;
			Chart.register(...chartModule.registerables);

			// Lade initiale Ergebnisse
			const resultsData = await getResults();
			setResults(resultsData);

		} catch (error) {
			console.error('Fehler beim Laden der Ergebnisse:', error);
			setError('Verbindung zum Server fehlgeschlagen.');
		} finally {
			loading.set(false);

			// Warte bis DOM aktualisiert wurde (Canvas ist jetzt gerendert)
			await new Promise(resolve => setTimeout(resolve, 50));

			// Erstelle Chart nachdem loading=false und Canvas gerendert ist
			createChart();

			// Starte WebSocket-Verbindung für Live-Updates
			startWebSocket();
		}
	});

	/**
	 * Cleanup beim Verlassen der Seite
	 */
	onDestroy(() => {
		if (wsClient) {
			wsClient.disconnect();
		}
		if (chartInstance) {
			chartInstance.destroy();
		}
	});

	/**
	 * Startet WebSocket-Verbindung für Live-Updates
	 */
	function startWebSocket() {
		wsClient = new WebSocketClient();

		// Listener für Ergebnis-Updates
		wsClient.on('results_update', (data) => {
			setResults({
				results: data.results,
				total_votes: data.total_votes
			});
			updateChart();
		});

		// Listener für neue Stimmen
		wsClient.on('vote_cast', (data) => {
			// Optional: Animation oder Benachrichtigung
			console.log(`Neue Stimme für ${data.candidate_name}`);
		});

		// Listener für Reset
		wsClient.on('reset', (data) => {
			showNotification(data.message, 'warning');
		});

		// Listener für Unlock
		wsClient.on('unlock', (data) => {
			showNotification(data.message || 'Neue Abstimmungsrunde gestartet!', 'info');
			// Leite zur Homepage weiter
			setTimeout(() => {
				goto('/');
			}, 1500);
		});

		// Listener für initiale Daten
		wsClient.on('initial_data', (data) => {
			setResults({
				results: data.results,
				total_votes: data.total_votes
			});
			updateChart();
		});

		wsClient.connect();
	}

	/**
	 * Erstellt das Chart
	 */
	function createChart() {
		if (!Chart) {
			console.error('Chart.js nicht geladen');
			return;
		}

		if (!chartCanvas) {
			console.error('Chart Canvas Element nicht gefunden');
			return;
		}

		const ctx = chartCanvas.getContext('2d');

		chartInstance = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: [],
				datasets: [
					{
						label: 'Stimmen',
						data: [],
						backgroundColor: 'rgba(139, 92, 246, 0.8)',
						borderColor: 'rgba(139, 92, 246, 1)',
						borderWidth: 2,
						borderRadius: 8
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: false
					},
					title: {
						display: true,
						text: 'Live-Abstimmungsergebnisse',
						font: {
							size: 20,
							weight: 'bold'
						}
					},
					tooltip: {
						callbacks: {
							label: function (context) {
								const value = context.parsed.y;
								const total = $results.total_votes;
								const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
								return `${value} Stimmen (${percentage}%)`;
							}
						}
					}
				},
				scales: {
					y: {
						beginAtZero: true,
						ticks: {
							stepSize: 1
						}
					}
				},
				animation: {
					duration: 750
				}
			}
		});

		updateChart();
	}

	/**
	 * Aktualisiert das Chart mit neuen Daten
	 */
	function updateChart() {
		if (!chartInstance) return;

		const sortedResults = [...$results.results].sort((a, b) => b.vote_count - a.vote_count);

		chartInstance.data.labels = sortedResults.map((r) => r.candidate_name);
		chartInstance.data.datasets[0].data = sortedResults.map((r) => r.vote_count);

		chartInstance.update();
	}

	/**
	 * Reaktiv: Update Chart wenn sich Ergebnisse ändern
	 */
	$: if ($results && chartInstance) {
		updateChart();
	}

	/**
	 * Berechnet die Farbe basierend auf Ranking
	 */
	function getRankColor(index) {
		const colors = [
			'bg-gradient-to-r from-yellow-400 to-yellow-500', // Gold
			'bg-gradient-to-r from-gray-300 to-gray-400', // Silber
			'bg-gradient-to-r from-orange-400 to-orange-500', // Bronze
			'bg-gradient-to-r from-[#f0f2f0] to-[#000c40]' // Andere
		];
		return colors[Math.min(index, colors.length - 1)];
	}

	/**
	 * Sortierte Ergebnisse für Listenansicht
	 */
	$: sortedResultsList = [...$resultsWithPercentage].sort(
		(a, b) => b.vote_count - a.vote_count
	);
</script>

<div class="min-h-screen py-8 px-4 fade-in">
	<div class="max-w-6xl mx-auto">
		<!-- Header -->
		<div class="text-center mb-8">
			<h1 class="text-5xl font-bold text-white mb-4">Live-Ergebnisse</h1>
			<div class="bg-white bg-opacity-20 backdrop-blur-lg rounded-full px-8 py-3 inline-block">
				<p class="text-2xl font-semibold text-white">
					Gesamt: {$results.total_votes} Stimmen
				</p>
			</div>
		</div>

		{#if $loading}
			<!-- Ladezustand -->
			<div class="text-center">
				<div
					class="inline-block animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white"
				></div>
				<p class="text-white mt-4 text-lg">Lade Ergebnisse...</p>
			</div>
		{:else}
			<!-- Content Container -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
				<!-- Chart -->
				<div class="bg-white rounded-2xl shadow-2xl p-6">
					<div class="h-[420px]">
						<canvas bind:this={chartCanvas}></canvas>
					</div>
				</div>

				<!-- Detaillierte Liste -->
				<div class="bg-white rounded-2xl shadow-2xl p-6 flex flex-col" style="height: 492px;">
					<h2 class="text-2xl font-bold text-gray-800 mb-6">Detaillierte Ergebnisse</h2>

					{#if sortedResultsList.length === 0}
						<div class="text-center py-12">
							<div class="text-6xl mb-4">📊</div>
							<p class="text-gray-600 text-lg">Noch keine Stimmen abgegeben</p>
						</div>
					{:else}
						<div class="space-y-4 overflow-y-auto px-1 flex-1">
							{#each sortedResultsList as result, index}
								<div class="result-item {getRankColor(index)} rounded-xl p-4 shadow-md mx-1">
									<div class="flex items-center justify-between mb-2">
										<div class="flex items-center gap-3">
											<div class="text-3xl font-bold text-white">
												{index + 1}
											</div>
											<div>
												<h3 class="text-xl font-bold text-white">
													{result.candidate_name}
												</h3>
												{#if result.description}
													<p class="text-white text-sm opacity-90">
														{result.description}
													</p>
												{/if}
											</div>
										</div>
										<div class="text-right">
											<div class="text-2xl font-bold text-white">
												{result.vote_count}
											</div>
											<div class="text-sm text-white opacity-90">
												{result.percentage}%
											</div>
										</div>
									</div>

									<!-- Progress Bar -->
									<div class="h-2 bg-white bg-opacity-30 rounded-full overflow-hidden">
										<div
											class="h-full bg-white transition-all duration-500"
											style="width: {result.percentage}%"
										></div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- Navigation -->
			<div class="text-center mt-8">
				<button
					on:click={() => goto('/')}
					class="bg-white text-[#000c40] px-8 py-3 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg"
				>
					Zurück zur Abstimmung
				</button>
			</div>

			<!-- Live-Indikator -->
			<div class="fixed bottom-8 right-8">
				<div
					class="bg-green-500 rounded-full px-6 py-3 shadow-lg flex items-center gap-3 animate-pulse"
				>
					<div class="w-3 h-3 bg-white rounded-full"></div>
					<span class="font-semibold text-white">Live</span>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.result-item {
		transition: transform 0.2s;
	}

	.result-item:hover {
		transform: scale(1.02);
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.7;
		}
	}

	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
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
