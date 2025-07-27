<script>
	let name = $state('world');
	let count = $state(0);
</script>

<h1>Hello {name}!</h1>

No idea waht version of Svelte this works on.

<input bind:value={name} />
<button onclick={() => count += 1}>
	clicks: {count}
</button>
