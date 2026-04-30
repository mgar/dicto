<template>
	<footer class="footer">
		<div class="footer-inner">
			<span class="brand">dicto</span>
			<span class="dot">•</span>
			<span class="muted">Built for daily Spanish practice</span>
			<span class="spacer"></span>
			<span class="muted">© {{ year }}</span>
		</div>
	</footer>
</template>

<script setup>
const year = new Date().getFullYear();
</script>

<style scoped>
.footer {
	margin-top: 20px;
	border-top: 1px solid var(--border-subtle);
	background: var(--transparent);
}

.footer-inner {
	max-width: 1120px;
	margin: 0 auto;
	padding: 14px 20px;
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 12.5px;
}

.brand {
	font-weight: 700;
	font-size: 13px;
	background: var(--accent-violet-gradient);
	-webkit-background-clip: text;
	-webkit-text-fill-color: var(--transparent);
	background-clip: text;
	letter-spacing: -0.4px;
}

.dot {
	color: var(--border-color);
}

.spacer {
	flex: 1;
}

@media (max-width: 640px) {
	.dot,
	.footer-inner .muted:first-of-type {
		display: none;
	}
}
</style>
