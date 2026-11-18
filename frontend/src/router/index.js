import { createRouter, createWebHistory } from "vue-router";
const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/LandingView.vue"),
  },
  {
    path: "/campus",
    name: "campus",
    component: () => import("../views/CampusSceneView.vue"),
  },
  {
    path: "/map",
    name: "map",
    component: () => import("../views/HomeView.vue"),
  },
  {
    path: "/campus/admin",
    name: "campus-admin",
    component: () => import("../views/CampusAdminView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
