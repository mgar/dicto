<template>
  <div class="app-shell">
    <AppNavbar />
    <div class="app-main">
      <main class="container">
        <RouterView />
      </main>
    </div>
    <AppFooter v-if="showFooter" />
  </div>
</template>

<script setup>

</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');


</style>
