<template>
  <main
    class="landing"
    :class="{ 'is-entering': entering, 'theme-light': theme === 'light' }"
  >
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-copy">
        <div id="hero-title">iNCUCampus</div>
        <div class="sub-title">串聯校園資訊，打造更便利的智慧生活。</div>
        <!-- <button
          class="explore-button"
          type="button"
          :disabled="entering"
          @click="enterCampus"
        >
        </button> -->
      </div>

      <div class="atlas">
        <svg
          ref="gridPattern"
          class="animated-grid-pattern"
          :viewBox="`0 0 ${gridWidth} ${gridHeight}`"
          preserveAspectRatio="none"
          aria-hidden="true"
          focusable="false"
        >
          <rect
            v-for="square in gridSquares"
            :key="square.id"
            class="grid-square"
            :x="square.x"
            :y="square.y"
            :width="gridSize - 1"
            :height="gridSize - 1"
            fill="currentColor"
            :style="{
              animationDelay: `${square.delay}s`,
              animationDuration: `${square.duration}s`,
              '--square-opacity': square.opacity,
            }"
          />
        </svg>
        <button
          class="island-button"
          type="button"
          :disabled="entering"
          aria-label="從台灣前往桃園國立中央大學地圖"
          @click="enterCampus"
        >
          <span
            class="taiwan"
            :style="{
              '--campus-focus-x': `${campusFocus.x}%`,
              '--campus-focus-y': `${campusFocus.y}%`,
            }"
            aria-hidden="true"
          >
            <svg
              class="island-svg"
              :viewBox="svgViewBox"
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <linearGradient id="island-fill" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stop-color="#223342" />
                  <stop offset="0.55" stop-color="#132330" />
                  <stop offset="1" stop-color="#0a171f" />
                </linearGradient>
                <filter
                  id="island-glow"
                  x="-50%"
                  y="-50%"
                  width="200%"
                  height="200%"
                >
                  <feGaussianBlur stdDeviation="0.12" />
                </filter>
                <radialGradient id="city-light">
                  <stop offset="0" stop-color="#fff9db" stop-opacity="0.95" />
                  <stop
                    offset="0.25"
                    stop-color="#ffe4a0"
                    stop-opacity="0.72"
                  />
                  <stop offset="1" stop-color="#ffce78" stop-opacity="0" />
                </radialGradient>
                <clipPath id="taiwan-coastline">
                  <path :d="islandPath" />
                </clipPath>
              </defs>
              <path
                :d="islandPath"
                fill="#80f2ed"
                opacity="0.2"
                filter="url(#island-glow)"
              />
              <path :d="islandPath" fill="url(#island-fill)" />
              <g clip-path="url(#taiwan-coastline)">
                <circle
                  v-for="light in cityLights"
                  :key="light.name"
                  :cx="light.longitude"
                  :cy="47.3 - light.latitude"
                  :r="light.radius"
                  fill="url(#city-light)"
                  :opacity="light.opacity"
                />
                <circle
                  v-for="(light, index) in lightSpecks"
                  :key="`speck-${index}`"
                  :cx="light.longitude"
                  :cy="47.3 - light.latitude"
                  :r="light.radius"
                  :opacity="light.opacity"
                  fill="#fff1bd"
                />
              </g>
              <path class="island-outline" :d="islandPath" />
            </svg>
          </span>
        </button>
      </div>
    </section>
    <div class="entry-transition" aria-hidden="true"></div>
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import taiwan from "../assets/taiwan.geojson?raw";

const router = useRouter();
const entering = ref(false);
const theme = ref("dark");
const gridSize = 40;
const gridPattern = ref(null);
const gridWidth = ref(1);
const gridHeight = ref(1);
const gridSquares = ref([]);

function updateGridSquares() {
  if (!gridPattern.value) return;

  const { width, height, left, top } =
    gridPattern.value.getBoundingClientRect();
  gridWidth.value = width;
  gridHeight.value = height;
  const firstColumn = Math.ceil(left / gridSize);
  const lastColumn = Math.floor((left + width - gridSize) / gridSize);
  const firstRow = Math.ceil(top / gridSize);
  const lastRow = Math.floor((top + height - gridSize) / gridSize);
  const cells = [];

  for (let row = firstRow; row <= lastRow; row += 1) {
    for (let column = firstColumn; column <= lastColumn; column += 1) {
      cells.push({ column, row });
    }
  }

  // Shuffle the visible cells so the highlights have no diagonal or repeated pattern.
  for (let index = cells.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [cells[index], cells[other]] = [cells[other], cells[index]];
  }

  gridSquares.value = cells
    .slice(0, Math.min(85, cells.length))
    .map((cell, id) => ({
      id,
      x: cell.column * gridSize - left + 1,
      y: cell.row * gridSize - top + 1,
      delay: -(Math.random() * 8),
      duration: 3 + Math.random() * 4,
      opacity: 0.06 + Math.random() * 0.08,
    }));
}

onMounted(() => {
  updateGridSquares();
  window.addEventListener("resize", updateGridSquares);
});
// The silhouette comes from the published TWN GeoJSON, rather than a hand-drawn outline.
const coordinates = JSON.parse(taiwan).features[0].geometry.coordinates[0];
const bounds = { left: 119.9, top: 21.7, width: 2.3, height: 3.9 };
const svgViewBox = `${bounds.left} ${bounds.top} ${bounds.width} ${bounds.height}`;
// National Central University, expressed in the SVG's flipped latitude coordinates.
const campusFocus = {
  x: ((121.194 - bounds.left) / bounds.width) * 100,
  y: ((47.3 - 24.968 - bounds.top) / bounds.height) * 100,
};
const islandPath =
  coordinates
    .map(
      ([longitude, latitude], index) =>
        `${index === 0 ? "M" : "L"}${longitude} ${47.3 - latitude}`
    )
    .join(" ") + " Z";
// Approximate urban light concentrations from the linked NASA night-light article.
const cityLights = [
  {
    name: "台北新北",
    longitude: 121.52,
    latitude: 25.06,
    radius: 0.42,
    opacity: 1,
  },
  {
    name: "基隆",
    longitude: 121.74,
    latitude: 25.12,
    radius: 0.16,
    opacity: 0.9,
  },
  {
    name: "桃園",
    longitude: 121.29,
    latitude: 24.99,
    radius: 0.32,
    opacity: 0.95,
  },
  {
    name: "新竹",
    longitude: 120.98,
    latitude: 24.8,
    radius: 0.25,
    opacity: 0.95,
  },
  {
    name: "苗栗",
    longitude: 120.81,
    latitude: 24.56,
    radius: 0.19,
    opacity: 0.72,
  },
  { name: "台中", longitude: 120.67, latitude: 24.15, radius: 0.4, opacity: 1 },
  {
    name: "彰化",
    longitude: 120.52,
    latitude: 24.06,
    radius: 0.24,
    opacity: 0.85,
  },
  {
    name: "宜蘭",
    longitude: 121.75,
    latitude: 24.75,
    radius: 0.17,
    opacity: 0.7,
  },
  {
    name: "南投",
    longitude: 120.69,
    latitude: 23.91,
    radius: 0.11,
    opacity: 0.48,
  },
];
// Deterministic small lights form a denser western corridor, without scattering
// stars over the central mountain range or needing any image or runtime request.
const lightSpecks = Array.from({ length: 230 }, (_, index) => {
  const random = (seed) => {
    const value = Math.sin(seed * 127.1 + 78.233) * 43758.5453;
    return value - Math.floor(value);
  };
  const latitude = 23.55 + random(index + 1) * 1.72;
  const westToEast = (latitude - 23.55) / 1.72;
  return {
    longitude: 120.42 + westToEast * 0.8 + random(index + 487) * 0.46,
    latitude,
    radius: 0.003 + random(index + 913) * 0.008,
    opacity: 0.3 + random(index + 151) * 0.55,
  };
});
let navigationTimer;

function enterCampus() {
  if (entering.value) return;
  theme.value =
    localStorage.getItem("campus-theme") === "light" ? "light" : "dark";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    router.push("/campus");
    return;
  }
  entering.value = true;
  navigationTimer = window.setTimeout(() => router.push("/campus"), 1400);
}

onBeforeUnmount(() => {
  window.clearTimeout(navigationTimer);
  window.removeEventListener("resize", updateGridSquares);
});
</script>

<style scoped>
.landing {
  --mint: #a2f6df;
  position: relative;
  display: flex;
  min-height: 100svh;
  flex-direction: column;
  overflow: hidden;
  background: #222426;
  color: #eaf7f5;
  isolation: isolate;
  height: 100vh;
}
.landing::before {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(#ffffff17 1px, transparent 1px),
    linear-gradient(90deg, #ffffff17 1px, transparent 1px);
  background-size: 40px 40px;
  content: "";
  pointer-events: none;
}
.landing-glow {
  position: absolute;
  top: 10%;
  right: 0%;
  z-index: -1;
  width: 100vw;
  height: 115vw;
  max-height: 1100px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    #ffffff70 0%,
    #00000040 34%,
    transparent 69%
  );
  filter: blur(45px);
  pointer-events: none;
}
.topbar,
.landing-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  width: 100%;
}
.topbar {
  position: relative;
  z-index: 2;
  padding: 29px clamp(28px, 5vw, 88px);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #f4ffff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-decoration: none;
  white-space: nowrap;
}
.brand-symbol {
  color: var(--mint);
  font-size: 28px;
  line-height: 1;
}
.brand-divider {
  color: #77a9b1;
  margin: 0 4px;
}
.topbar-caption,
.topbar-link,
.landing-footer,
.atlas-header,
.atlas-footer {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}
.topbar-caption {
  color: #7695a2;
}
.topbar-link {
  color: var(--mint);
  text-decoration: none;
  white-space: nowrap;
}
.topbar-link:hover {
  text-decoration: underline;
}
.hero {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  width: min(100%, 1600px);
  margin: 0 auto;
  padding: 25px clamp(28px, 7vw, 112px) 60px;
}
.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  z-index: 1;
  animation: reveal-copy 0.9s ease-out both;
}
@keyframes reveal-copy {
  from {
    opacity: 0;
    transform: translateY(-36px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.eyebrow {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 34px;
  color: var(--mint);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.19em;
}
.eyebrow-line {
  width: 23px;
  height: 1px;
  background: currentColor;
}
#hero-title {
  color: #ffffff;
  font-family: "Google Sans", Roboto, Arial, sans-serif;
  margin-top: 50px;
  font-size: clamp(42px, 5.2vw, 86px);
}
.sub-title {
  color: #ffffffce;
  font-family: "Google Sans", Roboto, Arial, sans-serif;
  margin-top: 20px;
}
.animated-grid-pattern {
  position: absolute;
  top: 0;
  left: 50%;
  display: block;
  width: min(100vw, 1600px);
  height: min(640px, 100svh);
  color: #ffffff;
  overflow: hidden;
  mask-image: linear-gradient(to bottom, black 65%, transparent 100%);
  pointer-events: none;
  transform: translateX(-50%);
}
.grid-square {
  opacity: 0;
  animation: grid-fade 3s ease-in-out infinite;
}
@keyframes grid-fade {
  40% {
    opacity: var(--square-opacity);
  }
  100% {
    opacity: 0;
  }
}
.intro {
  margin: 32px 0 35px;
  color: #a2b9c2;
  font-size: clamp(13px, 1.25vw, 16px);
  line-height: 2;
  letter-spacing: 0.02em;
}
.explore-button {
  display: inline-flex;
  min-height: 57px;
  align-items: center;
  gap: 16px;
  padding: 8px 20px 8px 9px;
  border: 1px solid #b5fff0;
  border-radius: 4px;
  background: var(--mint);
  color: #071f29;
  font-weight: 800;
  letter-spacing: 0.07em;
  transition: transform 0.25s, box-shadow 0.25s;
}
.explore-button:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 12px 36px #87f9dc3d;
}
.explore-button:disabled,
.island-button:disabled {
  cursor: wait;
}
.explore-icon {
  display: grid;
  width: 39px;
  height: 39px;
  place-items: center;
  border-radius: 2px;
  background: #092d37;
  color: var(--mint);
  font-size: 20px;
}
.explore-arrow {
  margin-left: 22px;
  font-size: 19px;
  font-weight: 400;
}
.hero-hint {
  margin: 18px 0 0;
  color: #7997a5;
  font-size: 11px;
  letter-spacing: 0.06em;
}
.atlas {
  position: relative;
  width: min(100%, 720px);
  min-height: min(65vw, 700px);
  margin-top: 20px;
}
.atlas-header,
.atlas-footer {
  position: absolute;
  z-index: 2;
  right: 0;
  left: 0;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  color: #8daab3;
}
.atlas-header {
  top: 2%;
}
.atlas-footer {
  bottom: 0;
}
.footer-arrow {
  color: var(--mint);
  font-size: 15px;
}
.island-button {
  position: absolute;
  inset: 4% 0;
  z-index: 1;
  width: 100%;
  padding: 0;
  overflow: visible;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  animation: reveal-island 1s ease-out 0.15s both;
}
@keyframes reveal-island {
  from {
    opacity: 0;
    transform: translateY(48px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.atlas-grid {
  position: absolute;
  inset: 9% 0;
  background: radial-gradient(
      circle at 50% 48%,
      #26878e19 0 30%,
      transparent 62%
    ),
    repeating-radial-gradient(
      circle at 50% 50%,
      transparent 0 74px,
      #94e9e912 75px 76px
    );
  mask-image: linear-gradient(90deg, transparent, black 20% 80%, transparent);
}
.orbit {
  position: absolute;
  top: 50%;
  left: 50%;
  width: min(85%, 590px);
  aspect-ratio: 1;
  border: 1px solid #7cdbd029;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}
.orbit-one::before {
  position: absolute;
  top: 13%;
  left: 15%;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--mint);
  box-shadow: 0 0 15px var(--mint);
  content: "";
}
.orbit-two {
  width: min(62%, 430px);
  border-color: #85e5dd20;
}
.taiwan {
  position: absolute;
  top: 70%;
  left: 50%;
  width: 102%;
  height: 160%;
  transform: translate(-50%, -50%);
  transform-origin: var(--campus-focus-x) var(--campus-focus-y);
  transition: transform 0.9s cubic-bezier(0.2, 0.75, 0.2, 1);
  filter: drop-shadow(16px 18px 25px #020914b3);
}
.island-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}
.island-outline {
  fill: none;
  stroke: #ffffff;
  stroke-width: 2px;
  vector-effect: non-scaling-stroke;
}
.location-dot {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 3px solid #eafff8;
  border-radius: 50%;
  background: #5effdb;
  box-shadow: 0 0 0 8px #66ffe42b, 0 0 28px 10px #5effdbba;
  transform: translate(-50%, -50%);
}
.location-dot::after {
  position: absolute;
  inset: -14px;
  border: 1px solid #aaffed77;
  border-radius: 50%;
  content: "";
  animation: pulse 2.6s ease-out infinite;
}
.location-label {
  position: absolute;
  top: 17%;
  right: 1%;
  display: grid;
  gap: 6px;
  padding: 13px 17px;
  border: 1px solid #86eadd42;
  border-radius: 3px;
  background: #102f3fbb;
  box-shadow: 0 12px 38px #0512208c;
  text-align: left;
  backdrop-filter: blur(10px);
  transition: opacity 0.4s;
}
.location-label::before {
  position: absolute;
  top: 50%;
  right: 100%;
  width: 50px;
  border-top: 1px dashed #8affdf9e;
  content: "";
}
.label-kicker {
  color: var(--mint);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.15em;
}
.location-label strong {
  font-size: 15px;
  letter-spacing: 0.05em;
}
.location-label small {
  color: #9bb9bd;
  font-size: 9px;
  letter-spacing: 0.12em;
}
.island-caption {
  position: absolute;
  bottom: 12%;
  left: 6%;
  color: #9cd3d1;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.26em;
}
.island-caption span {
  margin-left: 8px;
  color: var(--mint);
}
.island-button:hover .orbit-one {
  border-color: #a2f6df88;
}
.island-button:hover .taiwan {
  transform: translate(-50%, -50%) scale(1.045);
}
.is-entering .taiwan,
.is-entering .island-button:hover .taiwan {
  transform: translate(-50%, -50%) scale(1.6);
}
.is-entering .island-button {
  z-index: 5;
  pointer-events: none;
}
.entry-transition {
  position: fixed;
  inset: 0;
  z-index: 6;
  background: #222426;
  opacity: 0;
  pointer-events: none;
}
.theme-light .entry-transition {
  background: #f5f6f1;
}
.is-entering .entry-transition {
  animation: fill-entry 0.7s ease-in 0.55s forwards;
}
@keyframes fill-entry {
  to {
    opacity: 1;
  }
}
.is-entering .location-label,
.is-entering .island-caption,
.is-entering .hero-copy,
.is-entering .atlas-header,
.is-entering .atlas-footer {
  opacity: 0;
  transition: opacity 0.45s;
}
.is-entering .landing-glow {
  transform: scale(2);
  transition: transform 1.3s;
}
.landing-footer {
  padding: 20px clamp(28px, 5vw, 88px);
  border-top: 1px solid #9cdbd01a;
  color: #839da7;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
@keyframes pulse {
  to {
    opacity: 0;
    transform: scale(2.2);
  }
}
@media (max-width: 1000px) {
  .topbar-caption {
    display: none;
  }
  .hero {
    grid-template-columns: 1fr;
    gap: 0;
    padding-top: 80px;
  }
  .hero-copy {
    padding-bottom: 0;
  }
  .atlas {
    min-height: clamp(430px, 76vw, 650px);
  }
  .landing-footer span:nth-child(2) {
    display: none;
  }
}
@media (max-width: 580px) {
  .topbar {
    padding: 22px 20px;
  }
  .brand {
    font-size: 10px;
    letter-spacing: 0.07em;
  }
  .topbar-link {
    font-size: 10px;
    letter-spacing: 0;
  }
  .hero {
    padding: 48px 23px 40px;
  }
  .eyebrow {
    margin-bottom: 24px;
    font-size: 8px;
  }
  h1 {
    font-size: clamp(34px, 8.4vw, 50px);
  }
  .intro {
    margin: 24px 0;
  }
  .atlas {
    min-height: 430px;
    margin: 20px -12px 0;
  }
  .atlas-header,
  .atlas-footer {
    font-size: 8px;
  }
  .taiwan {
    width: 120%;
  }
  .location-label {
    right: 0;
    padding: 10px;
  }
  .location-label::before {
    width: 22px;
  }
  .location-label strong {
    font-size: 12px;
  }
  .landing-footer {
    padding: 17px 20px;
    font-size: 8px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .hero-copy,
  .island-button {
    animation: none;
  }
  .entry-transition {
    animation: none;
  }
  .grid-square {
    animation: none;
    opacity: 0.06;
  }
  .location-dot::after {
    animation: none;
  }
  .taiwan,
  .explore-button {
    transition: none;
  }
}
</style>
