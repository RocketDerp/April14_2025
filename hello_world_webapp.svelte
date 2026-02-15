<script>
	let name = $state('world');
	let count = $state(0);
</script>

<h1>Hello {name}!</h1>

No idea what version of Svelte this works on.

<BR />

    Markdown to HTML conversion published currently at: <A HREF="https://RocketDerp.GitHub.io/April14_2025/">https://RocketDerp.GitHub.io/April14_2025</A>

<BR />

<input bind:value={name} />
<button onclick={() => count += 1}>
	clicks: {count}
</button>
