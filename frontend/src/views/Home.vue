<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="max-w-4xl mx-auto text-center">
      <h1 class="text-4xl font-bold text-gray-900 mb-6">
        TorWAR
      </h1>
      <p class="text-xl text-gray-600 mb-8">
        AWS Well-Architected Review Tool
      </p>
      <div class="space-x-4">
        <router-link 
          to="/login"
          class="bg-primary-600 hover:bg-primary-700 text-white px-6 py-3 rounded-md font-medium"
        >
          Sign In
        </router-link>
        <router-link 
          to="/register"
          class="bg-gray-200 hover:bg-gray-300 text-gray-900 px-6 py-3 rounded-md font-medium"
        >
          Register
        </router-link>
      </div>
    </div>
  </div>
</template>
