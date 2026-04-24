<template>
  <div id="app">
    <header>
      <nav>
        <router-link to="/">Home</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
// No additional logic needed for Phase 1
</script>

<style scoped>
header {
  background-color: #2c3e50;
  padding: 1rem;
  color: white;
}

nav a {
  color: white;
  text-decoration: none;
  font-weight: bold;
}

nav a:hover {
  text-decoration: underline;
}

main {
  padding: 2rem;
}
</style>
