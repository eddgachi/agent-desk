<template>
  <div class="flex flex-col h-screen overflow-hidden bg-gray-50 text-gray-800 select-none">
    <!-- ── Header ─────────────────────────────────────────── -->
    <header
      class="flex-none flex items-center justify-between px-4 h-12 bg-gray-900 border-b border-gray-700 z-10 shadow-md"
    >
      <div class="flex items-center gap-4">
        <router-link
          to="/office"
          class="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          <span class="text-lg">◀</span>
          <span class="font-bold text-sm tracking-widest uppercase">AgentDesk</span>
        </router-link>
      </div>
      <div class="flex items-center gap-4 text-xs">
        <router-link to="/office" class="text-gray-400 hover:text-gray-200 transition-colors">Office</router-link>
        <span class="text-gray-600">·</span>
        <span class="text-indigo-400 font-semibold">About</span>
      </div>
    </header>

    <!-- ── Content ────────────────────────────────────────── -->
    <main class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-6 py-12 space-y-10">
        <!-- Hero -->
        <div class="text-center space-y-4">
          <h1 class="text-4xl font-bold text-gray-900 tracking-tight">AgentDesk</h1>
          <p class="text-lg text-gray-500 max-w-xl mx-auto leading-relaxed">
            An autonomous AI-agent office simulation — watch virtual workers collaborate, move through their workspace,
            and complete tasks in real time.
          </p>
        </div>

        <!-- Divider -->
        <div class="border-t border-gray-200" />

        <!-- How it works -->
        <section class="space-y-5">
          <h2 class="text-xl font-semibold text-gray-800">How It Works</h2>
          <div class="grid md:grid-cols-3 gap-6">
            <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-200 space-y-2">
              <div class="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600 text-lg">
                🧠
              </div>
              <h3 class="font-semibold text-gray-800">AI Agents</h3>
              <p class="text-sm text-gray-500 leading-relaxed">
                Each agent has a role, personality, and goals. They decide their own actions — working, meeting, taking
                breaks — just like a real team.
              </p>
            </div>
            <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-200 space-y-2">
              <div
                class="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600 text-lg"
              >
                🏢
              </div>
              <h3 class="font-semibold text-gray-800">Living Office</h3>
              <p class="text-sm text-gray-500 leading-relaxed">
                A top-down blueprint-style office with desks, meeting rooms, a break area, and hallways — all rendered
                as an interactive simulation map.
              </p>
            </div>
            <div class="bg-white rounded-xl p-5 shadow-sm border border-gray-200 space-y-2">
              <div class="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600 text-lg">
                ⚡
              </div>
              <h3 class="font-semibold text-gray-800">Real-time Events</h3>
              <p class="text-sm text-gray-500 leading-relaxed">
                Every action generates an event. Watch the activity feed as agents start tasks, chat with colleagues,
                grab coffee, or head to meetings.
              </p>
            </div>
          </div>
        </section>

        <!-- Divider -->
        <div class="border-t border-gray-200" />

        <!-- Tech stack -->
        <section class="space-y-5">
          <h2 class="text-xl font-semibold text-gray-800">Tech Stack</h2>
          <div class="flex flex-wrap gap-3">
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">Vue.js</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">FastAPI</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">WebSockets</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">Canvas API</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">Docker</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">Tailwind CSS</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">PostgreSQL</span>
            <span class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600 font-medium">Redis</span>
          </div>
        </section>

        <!-- Divider -->
        <div class="border-t border-gray-200" />

        <!-- Footer -->
        <div class="text-center text-sm text-gray-400 pb-8">
          AgentDesk — built for exploring emergent behaviour in multi-agent systems.
        </div>
      </div>
    </main>
  </div>
</template>

<script setup></script>
