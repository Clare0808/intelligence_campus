<template>
  <div class="campus-app">
    <header class="topbar">
      <a class="brand" href="#main-content" aria-label="中央大學校園地圖首頁">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32">
            <path d="M5 24.5 15.8 5l11.1 19.5H5Z" />
            <path d="M12 24.5 18.2 13l6.5 11.5" />
            <path d="M4 27h24" />
          </svg>
        </span>
        <span class="brand-name">NCU <span>校園地圖</span></span>
      </a>
      <!-- <nav class="top-nav" aria-label="主要導覽">
        <a class="nav-link active" href="#explore">探索地圖</a>
        <a class="nav-link" href="#directory">地點列表</a>
        <a class="nav-link" href="#about-map">地圖說明</a>
      </nav> -->
      <a
        class="campus-link"
        href="https://www.ncu.edu.tw/"
        target="_blank"
        rel="noopener noreferrer"
      >
        中央大學網站 <span aria-hidden="true">↗</span>
      </a>
    </header>

    <main id="main-content">
      <section id="explore" class="intro">
        <div>
          <div class="eyebrow">
            <span class="eyebrow-dot"></span> 國立中央大學
          </div>
          <h1>漫遊校園，<span>找到你的目的地。</span></h1>
          <p>探索校園地點與步行路線，認識中央大學的每個角落。</p>
        </div>
        <div class="campus-note">
          <span class="note-icon" aria-hidden="true">✳</span>
          <span
            ><strong>從這裡開始探索</strong
            ><small>校園地點，一覽即知</small></span
          >
        </div>
      </section>

      <div class="workspace">
        <aside id="directory" class="directory panel">
          <div class="panel-heading directory-heading">
            <div>
              <span class="section-kicker">校園地點索引</span>
              <h2>
                探索地點
                <span class="place-count">{{ filteredBuildings.length }}</span>
              </h2>
            </div>
            <button
              v-if="activeCategory || searchQuery"
              class="clear-button"
              type="button"
              @click="clearFilters"
            >
              清除
            </button>
          </div>

          <label class="search-box">
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <circle cx="8.7" cy="8.7" r="5.6" />
              <path d="m13 13 4 4" />
            </svg>
            <span class="sr-only">搜尋校園地點</span>
            <input
              v-model="searchQuery"
              type="search"
              placeholder="搜尋地點名稱..."
            />
            <kbd>/</kbd>
          </label>

          <div class="category-filters" aria-label="依類別篩選地點">
            <button
              class="filter-chip"
              :class="{ chosen: activeCategory === '' }"
              type="button"
              :aria-pressed="activeCategory === ''"
              @click="activeCategory = ''"
            >
              全部地點
            </button>
            <button
              v-for="category in categories"
              :key="category.id"
              class="filter-chip"
              :class="{ chosen: activeCategory === category.id }"
              type="button"
              :aria-pressed="activeCategory === category.id"
              @click="
                activeCategory =
                  activeCategory === category.id ? '' : category.id
              "
            >
              <span
                class="chip-dot"
                :style="{ '--chip-color': category.color }"
              ></span>
              {{ category.label }}
            </button>
          </div>

          <div class="list-caption">
            <span>地點</span>
            <span>{{ filteredBuildings.length }} 個結果</span>
          </div>
          <div class="place-list" role="list" aria-label="校園地點">
            <button
              v-for="building in filteredBuildings"
              :key="building.id"
              class="place-row"
              :class="{ selected: selectedId === building.id }"
              type="button"
              role="listitem"
              :aria-current="selectedId === building.id ? 'true' : null"
              @click="selectBuilding(building.id)"
            >
              <span
                class="place-symbol"
                :style="{
                  '--category-color': categoryFor(building.category).color,
                }"
              >
                {{ categoryFor(building.category).icon }}
              </span>
              <span class="place-copy">
                <strong>{{ building.name }}</strong>
                <small
                  >#{{ building.number }}・{{
                    categoryFor(building.category).label
                  }}</small
                >
              </span>
              <span class="row-arrow" aria-hidden="true">↗</span>
            </button>
            <div
              v-if="filteredBuildings.length === 0"
              class="empty-state"
              role="status"
            >
              <span aria-hidden="true">⌕</span>
              <strong>找不到符合的地點</strong>
              <p>請嘗試其他名稱，或清除分類篩選條件。</p>
              <button type="button" @click="clearFilters">顯示全部地點</button>
            </div>
          </div>
          <div class="directory-footer">
            <span class="footer-pin" aria-hidden="true">⌖</span>
            <span
              ><strong>開始認識校園</strong
              ><small>選擇地點以查看詳細資訊</small></span
            >
          </div>
        </aside>

        <section class="map-panel panel" aria-label="互動式校園地圖">
          <div class="map-toolbar">
            <div class="map-title">
              <span class="map-live-dot"></span>
              <span><strong>校園總覽</strong><small>國立中央大學</small></span>
            </div>
            <div class="map-actions">
              <span class="map-scale"
                >{{ buildings.length }} 個建物與入口・立體校園圖</span
              >
              <button
                class="icon-button"
                type="button"
                aria-label="放大地圖"
                @click="zoomMap(1)"
              >
                <span aria-hidden="true">+</span>
              </button>
              <button
                class="icon-button"
                type="button"
                aria-label="縮小地圖"
                @click="zoomMap(-1)"
              >
                <span aria-hidden="true">−</span>
              </button>
              <button
                class="icon-button reset-map"
                type="button"
                aria-label="重設地圖縮放"
                @click="mapZoom = 1"
              >
                <svg viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M4 8a6.2 6.2 0 1 1-.2 4M4 4v4h4" />
                </svg>
              </button>
            </div>
          </div>

          <div class="map-canvas">
            <svg
              class="campus-map"
              viewBox="0 0 1600 1100"
              role="group"
              aria-labelledby="map-title map-description"
              preserveAspectRatio="xMidYMid meet"
            >
              <title id="map-title">中央大學校園示意圖</title>
              <desc id="map-description">
                參考中央大學校園分區的原創互動式立體校園示意圖，包含道路、湖泊、綠地及建物。點選建物或使用地點列表探索。
              </desc>
              <g
                :transform="`translate(${800 - 800 * mapZoom} ${
                  550 - 550 * mapZoom
                }) scale(${mapZoom})`"
              >
                <rect width="1600" height="1100" fill="#e9eee3" />
                <path
                  class="campus-ground"
                  d="M266 117 509 46 778 79 1018 113 1369 217 1518 388 1461 614 1342 850 1068 1013 754 1051 420 964 175 819 105 608 155 344Z"
                />
                <path
                  class="campus-boundary"
                  d="M266 117 509 46 778 79 1018 113 1369 217 1518 388 1461 614 1342 850 1068 1013 754 1051 420 964 175 819 105 608 155 344Z"
                />
                <g class="campus-landscape" aria-hidden="true">
                  <path
                    class="landscape-grove"
                    d="M184 174 400 95 562 119 499 311 291 367 153 315Z"
                  />
                  <path
                    class="landscape-grove"
                    d="M1107 175 1369 241 1463 393 1333 473 1097 365Z"
                  />
                  <path
                    class="landscape-grove"
                    d="M128 550 333 588 378 795 232 824 141 722Z"
                  />
                  <path
                    class="landscape-field"
                    d="M230 368 385 371 415 606 288 614 228 529Z"
                  />
                  <path
                    class="landscape-field"
                    d="M1287 665 1401 622 1377 783 1232 874 1178 839Z"
                  />
                  <path
                    class="landscape-lake"
                    d="M606 351 C641 324 699 336 717 367 C731 392 713 426 676 435 C638 447 600 421 586 389 C578 372 591 358 606 351Z"
                  />
                  <path
                    class="lake-shine"
                    d="M608 375 Q649 345 687 369 M625 408 Q660 428 691 398"
                  />
                  <!-- OSM relation 5951533 places the athletics track west of
                       羽球館, extending north–south, not by the south gate. -->
                  <ellipse
                    class="athletic-track"
                    cx="320"
                    cy="492"
                    rx="58"
                    ry="104"
                    transform="rotate(-12 320 492)"
                  />
                  <ellipse
                    class="athletic-field"
                    cx="320"
                    cy="492"
                    rx="38"
                    ry="80"
                    transform="rotate(-12 320 492)"
                  />
                  <rect
                    class="sports-court"
                    x="1270"
                    y="688"
                    width="67"
                    height="37"
                    rx="4"
                    transform="rotate(-18 1270 688)"
                  />
                </g>
                <g class="campus-paths" aria-hidden="true">
                  <path
                    v-for="path in campusPaths"
                    :key="`bed-${path.id}`"
                    :d="path.d"
                    class="campus-road-bed"
                  />
                  <path
                    v-for="path in campusPaths"
                    :key="path.id"
                    :d="path.d"
                    class="campus-walkway"
                  />
                </g>
                <g class="landscape-labels" aria-hidden="true">
                  <text x="650" y="399">中大湖</text>
                  <text x="320" y="495">操場</text>
                  <text x="237" y="251">校園綠地</text>
                  <text x="1358" y="755">運動園區</text>
                  <text x="773" y="936">中大路・正門</text>
                  <text x="1444" y="110" class="map-north">N ↑</text>
                </g>

                <polyline
                  v-if="route"
                  :points="routePoints"
                  class="route-line"
                  :class="{ accessible: accessibleOnly }"
                  aria-hidden="true"
                />
                <g v-if="route" class="route-endpoints" aria-hidden="true">
                  <circle
                    :cx="route.points[0].x"
                    :cy="route.points[0].y"
                    r="14"
                    class="route-start"
                  />
                  <circle
                    :cx="route.points[route.points.length - 1].x"
                    :cy="route.points[route.points.length - 1].y"
                    r="14"
                    class="route-end"
                  />
                </g>

                <g
                  v-for="building in visibleBuildings"
                  :key="building.id"
                  class="isometric-building"
                  :class="{
                    selected: selectedId === building.id,
                    'route-stop': routeIds.includes(building.id),
                  }"
                  :transform="`translate(${building.x} ${building.y})`"
                  role="button"
                  tabindex="0"
                  :aria-label="`${building.name}，${
                    categoryFor(building.category).label
                  }，分區 ${building.zone}`"
                  :aria-pressed="selectedId === building.id"
                  @click="selectBuilding(building.id)"
                  @keydown.enter.prevent="selectBuilding(building.id)"
                  @keydown.space.prevent="selectBuilding(building.id)"
                  :style="{
                    '--building-color': categoryFor(building.category).color,
                  }"
                >
                  <title>{{ building.name }}・分區 {{ building.zone }}</title>
                  <polygon
                    v-if="building.shape !== 'gate'"
                    class="building-shadow"
                    :points="`-${building.width / 2},0 0,${
                      building.depth / 2
                    } ${building.width / 2},0 0,-${building.depth / 2}`"
                  />
                  <polygon
                    v-if="building.shape !== 'gate'"
                    class="building-left-face"
                    :points="`-${building.width / 2},-${building.height} 0,-${
                      building.height - building.depth / 2
                    } 0,${building.depth / 2} -${building.width / 2},0`"
                  />
                  <polygon
                    v-if="building.shape !== 'gate'"
                    class="building-right-face"
                    :points="`0,-${building.height - building.depth / 2} ${
                      building.width / 2
                    },-${building.height} ${building.width / 2},0 0,${
                      building.depth / 2
                    }`"
                  />
                  <polygon
                    v-if="
                      building.shape !== 'gate' && building.shape !== 'tower'
                    "
                    class="building-roof"
                    :points="`-${building.width / 2},-${building.height} 0,-${
                      building.height - building.depth / 2
                    } ${building.width / 2},-${building.height} 0,-${
                      building.height + building.depth / 2
                    }`"
                  />
                  <polygon
                    v-if="building.shape === 'tower'"
                    class="building-roof"
                    :points="`-${building.width / 2},-${building.height} 0,-${
                      building.height - building.depth / 2
                    } ${building.width / 2},-${building.height} 0,-${
                      building.height + building.depth / 2
                    }`"
                  />
                  <polygon
                    v-if="building.shape === 'hall'"
                    class="building-roof-accent"
                    :points="`-${building.width * 0.37},-${
                      building.height - building.depth * 0.02
                    } 0,-${building.height + building.depth * 0.23} ${
                      building.width * 0.37
                    },-${building.height - building.depth * 0.02} 0,-${
                      building.height + building.depth * 0.43
                    }`"
                  />
                  <polygon
                    v-if="building.shape === 'courtyard'"
                    class="building-roof-accent courtyard-opening"
                    :points="`-${building.width * 0.18},-${
                      building.height
                    } 0,-${building.height - building.depth * 0.12} ${
                      building.width * 0.18
                    },-${building.height} 0,-${
                      building.height + building.depth * 0.18
                    }`"
                  />
                  <polygon
                    v-if="building.shape === 'wing'"
                    class="building-roof-accent"
                    :points="`-${building.width * 0.39},-${
                      building.height
                    } 0,-${building.height - building.depth * 0.29} ${
                      building.width * 0.39
                    },-${building.height} 0,-${
                      building.height + building.depth * 0.29
                    }`"
                  />
                  <g
                    v-if="building.shape === 'courtyard'"
                    class="building-detail"
                    aria-hidden="true"
                  >
                    <path
                      :d="`M-${building.width * 0.22},-${building.height} 0,-${
                        building.height - building.depth * 0.16
                      } ${building.width * 0.22},-${building.height}`"
                    />
                    <path
                      :d="`M0,-${building.height - building.depth * 0.16} V-${
                        building.height + building.depth * 0.34
                      }`"
                    />
                  </g>
                  <g
                    v-if="building.shape === 'wing'"
                    class="building-detail"
                    aria-hidden="true"
                  >
                    <path
                      :d="`M-${building.width * 0.3},-${
                        building.height - 1
                      } 0,-${building.height - building.depth * 0.27} ${
                        building.width * 0.3
                      },-${building.height - 1}`"
                    />
                  </g>
                  <g
                    v-if="building.shape === 'hall'"
                    class="building-detail"
                    aria-hidden="true"
                  >
                    <path
                      :d="`M-${building.width * 0.32},-${
                        building.height - 2
                      } 0,-${building.height + building.depth * 0.3} ${
                        building.width * 0.32
                      },-${building.height - 2}`"
                    />
                  </g>
                  <g
                    v-if="building.shape === 'tower'"
                    class="building-detail"
                    aria-hidden="true"
                  >
                    <path
                      :d="`M0,-${
                        building.height + building.depth * 0.5
                      } v-13 m-6,6 h12`"
                    />
                  </g>
                  <g
                    v-if="building.shape === 'gate'"
                    class="building-gate"
                    aria-hidden="true"
                  >
                    <path
                      d="M-14 0 V-20 H14 V0 M-18 -22 H18 M-6 0 V-11 H6 V0"
                    />
                  </g>
                  <path
                    v-if="
                      building.shape !== 'gate' && building.shape !== 'tower'
                    "
                    class="building-windows"
                    :d="`M-${building.width / 2 + 5},-${building.height / 2} v${
                      building.height / 3
                    } M-${building.width / 2 + 11},-${building.height / 2} v${
                      building.height / 3
                    } M5,-${building.height / 2} v${building.height / 3} M11,-${
                      building.height / 2
                    } v${building.height / 3}`"
                  />
                  <text
                    class="building-number"
                    x="0"
                    :y="-building.height + building.depth / 8"
                  >
                    {{ building.number }}
                  </text>
                </g>
              </g>
            </svg>
            <div class="map-legend" aria-label="地圖圖例">
              <span v-for="category in categories" :key="category.id">
                <i :style="{ backgroundColor: category.color }"></i
                >{{ category.label }}
              </span>
            </div>
            <div v-if="route" class="route-map-badge">
              <span class="route-dot"></span> 路線 ·
              {{ formatDistance(route.distance) }}
            </div>
            <div class="map-attribution">
              原創立體校園示意圖・建物與路線位置尚未測繪
            </div>
          </div>
          <div class="map-bottom">
            <span
              ><span class="map-hint-icon">↖</span>
              選擇地圖標記或地點開始探索</span
            >
            <span class="map-status"><i></i> 載入後可離線瀏覽</span>
          </div>
        </section>

        <aside class="details-panel panel" aria-live="polite">
          <div
            class="detail-tabs"
            role="tablist"
            aria-label="地點資訊與路線指引"
          >
            <button
              id="place-tab"
              type="button"
              role="tab"
              :aria-selected="activeTab === 'place'"
              aria-controls="place-panel"
              :class="{ active: activeTab === 'place' }"
              @click="activeTab = 'place'"
            >
              地點資訊
            </button>
            <button
              id="directions-tab"
              type="button"
              role="tab"
              :aria-selected="activeTab === 'directions'"
              aria-controls="directions-panel"
              :class="{ active: activeTab === 'directions' }"
              @click="activeTab = 'directions'"
            >
              <svg viewBox="0 0 20 20" aria-hidden="true">
                <path d="M10 2.5 17 10l-7 7.5L3 10l7-7.5Z" />
                <path d="M10 6v8M6.5 10H13.5" />
              </svg>
              路線指引
            </button>
          </div>
          <div
            v-if="activeTab === 'place'"
            id="place-panel"
            role="tabpanel"
            aria-labelledby="place-tab"
            class="detail-content"
          >
            <div v-if="selectedBuilding" class="selected-place">
              <div class="detail-category">
                <span
                  class="detail-category-dot"
                  :style="{
                    backgroundColor: categoryFor(selectedBuilding.category)
                      .color,
                  }"
                ></span>
                {{ categoryFor(selectedBuilding.category).label }}
                <span class="detail-id"
                  >建物 #{{ selectedBuilding.number }}</span
                >
              </div>
              <h2>{{ selectedBuilding.name }}</h2>
              <p class="place-description">{{ selectedBuilding.detail }}</p>
              <div class="detail-divider"></div>
              <div class="info-heading">
                <span class="info-icon" aria-hidden="true">⌖</span
                ><strong>地點簡介</strong>
              </div>
              <p class="info-body">{{ selectedBuilding.short }}</p>
              <div class="access-card">
                <span class="access-icon" aria-hidden="true">♿</span>
                <div>
                  <strong>無障礙資訊</strong>
                  <p>{{ selectedBuilding.accessibility }}</p>
                  <span class="unverified-label"><i></i> 資訊尚待現場確認</span>
                </div>
              </div>
              <div class="detail-spacer"></div>
              <button
                class="primary-button"
                type="button"
                @click="prepareDirections(selectedBuilding.id)"
              >
                <svg viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M10 2.5 17 10l-7 7.5L3 10l7-7.5Z" />
                  <path d="M10 6v8M6.5 10H13.5" />
                </svg>
                規劃前往路線 <span aria-hidden="true">→</span>
              </button>
              <p class="data-note">
                建物名稱依官方導覽圖整理；位置與路線為示意，使用前請核對。
              </p>
            </div>
          </div>

          <div
            v-else
            id="directions-panel"
            role="tabpanel"
            aria-labelledby="directions-tab"
            class="detail-content directions-content"
          >
            <span class="section-kicker">步行路線規劃</span>
            <h2>規劃路線</h2>
            <p class="directions-intro">選擇起點與目的地，查看校園步行路線。</p>
            <label class="select-label" for="origin-select">起點</label>
            <div class="select-wrap">
              <span
                class="select-marker origin-marker"
                aria-hidden="true"
              ></span>
              <select
                id="origin-select"
                v-model="originId"
                aria-label="選擇起點"
              >
                <option
                  v-for="building in buildings"
                  :key="building.id"
                  :value="building.id"
                >
                  {{ building.name }}
                </option>
              </select>
            </div>
            <button
              class="swap-button"
              type="button"
              aria-label="交換起點與目的地"
              @click="swapPlaces"
            >
              ↕
            </button>
            <label class="select-label" for="destination-select">目的地</label>
            <div class="select-wrap">
              <span
                class="select-marker destination-marker"
                aria-hidden="true"
              ></span>
              <select
                id="destination-select"
                v-model="destinationId"
                aria-label="選擇目的地"
              >
                <option
                  v-for="building in buildings"
                  :key="building.id"
                  :value="building.id"
                >
                  {{ building.name }}
                </option>
              </select>
            </div>
            <label class="accessible-toggle">
              <input v-model="accessibleOnly" type="checkbox" />
              <span class="toggle-ui"></span>
              <span
                ><strong>無障礙路線</strong
                ><small>只採用已查證的無階差路段</small></span
              >
            </label>
            <button
              class="primary-button route-button"
              type="button"
              @click="showRoute = true"
            >
              <svg viewBox="0 0 20 20" aria-hidden="true">
                <path d="M10 2.5 17 10l-7 7.5L3 10l7-7.5Z" />
                <path d="M10 6v8M6.5 10H13.5" />
              </svg>
              查詢步行路線 <span aria-hidden="true">→</span>
            </button>
            <div v-if="showRoute && route" class="route-result" role="status">
              <div class="route-result-head">
                <span class="route-check" aria-hidden="true">✓</span>
                <span
                  ><strong>{{ formatDistance(route.distance) }} 步行路線</strong
                  ><small
                    >{{ route.points.length - 1 }} 個路段・預估
                    {{ estimateMinutes(route.distance) }} 分鐘</small
                  ></span
                >
              </div>
              <div class="route-steps">
                <div
                  v-for="(building, index) in route.buildings"
                  :key="building.id"
                  class="route-step"
                >
                  <span
                    class="step-marker"
                    :class="{ last: index === route.buildings.length - 1 }"
                  ></span>
                  <span
                    ><small>{{
                      index === 0
                        ? "起點"
                        : index === route.buildings.length - 1
                        ? "抵達"
                        : `途經 0${index}`
                    }}</small
                    ><strong>{{ building.name }}</strong></span
                  >
                </div>
              </div>
              <p class="route-disclaimer">
                路線距離為示意；實際路況與無階差通行條件尚未現場查證。
              </p>
            </div>
            <div
              v-else-if="showRoute && !route"
              class="route-unavailable"
              role="alert"
            >
              <span aria-hidden="true">!</span>
              <div>
                <strong>目前無可用路線</strong>
                <p>
                  {{
                    accessibleOnly
                      ? "目前沒有經現場查證的無階差路段資料，因此無法提供可確認的無障礙路線。"
                      : "示意路網中沒有連接這兩個地點的路線。"
                  }}
                </p>
              </div>
            </div>
            <div v-else class="route-tip">
              <span aria-hidden="true">✳</span>
              <p>
                無障礙路段尚未經現場查證；在取得校方資料前，不會將示意路線標示為無障礙。
              </p>
            </div>
            <div class="detail-spacer"></div>
            <p class="data-note">示意路網・實際路線請以校園現場資訊為準。</p>
          </div>
          <div class="detail-foot">
            <span>中央大學校園導覽</span>
            <span>陪你輕鬆找到目的地 <i aria-hidden="true">✳</i></span>
          </div>
        </aside>
      </div>

      <section id="about-map" class="map-disclaimer">
        <span class="disclaimer-symbol" aria-hidden="true">i</span>
        <p>
          <strong>地圖使用提醒</strong>
          本圖參考中央大學校園分區重新繪製，非官方地圖或精確測繪。建物造型、位置及路線為示意，不可作為現場導航依據。無障礙資訊尚未查證；正式使用前請向中央大學確認。
        </p>
        <span class="disclaimer-tag">示意資料</span>
      </section>
    </main>
    <footer class="site-footer">
      <span>© NCU 校園地圖</span>
      <span>讓校園地點更容易找到。</span>
    </footer>
  </div>
</template>

<script>
import { buildings, campusPaths, categories, findRoute } from "@/data/campus";

export default {
  name: "HomeView",
  data() {
    return {
      buildings,
      campusPaths,
      categories,
      searchQuery: "",
      activeCategory: "",
      selectedId: "2",
      activeTab: "place",
      originId: "42",
      destinationId: "2",
      accessibleOnly: false,
      showRoute: false,
      mapZoom: 1,
    };
  },
  computed: {
    filteredBuildings() {
      const query = this.searchQuery.trim().toLocaleLowerCase();
      return this.buildings.filter((building) => {
        const matchesQuery =
          !query ||
          building.name.toLocaleLowerCase().includes(query) ||
          building.short.toLocaleLowerCase().includes(query) ||
          this.categoryFor(building.category)
            .label.toLocaleLowerCase()
            .includes(query);
        return (
          matchesQuery &&
          (!this.activeCategory || building.category === this.activeCategory)
        );
      });
    },
    visibleBuildings() {
      return [...this.filteredBuildings].sort((a, b) => a.y - b.y);
    },
    selectedBuilding() {
      return this.buildings.find((building) => building.id === this.selectedId);
    },
    route() {
      if (!this.showRoute) return null;
      return findRoute(this.originId, this.destinationId, this.accessibleOnly);
    },
    routePoints() {
      return this.route
        ? this.route.points.map((point) => `${point.x},${point.y}`).join(" ")
        : "";
    },
    routeIds() {
      return this.route
        ? this.route.buildings.map((building) => building.id)
        : [];
    },
  },
  watch: {
    searchQuery() {
      this.keepSelectionVisible();
    },
    activeCategory() {
      this.keepSelectionVisible();
    },
    accessibleOnly() {
      this.showRoute = true;
    },
    originId() {
      this.showRoute = false;
    },
    destinationId() {
      this.showRoute = false;
    },
  },
  methods: {
    categoryFor(categoryId) {
      return (
        this.categories.find((category) => category.id === categoryId) ||
        this.categories[0]
      );
    },
    selectBuilding(id) {
      this.selectedId = id;
      this.activeTab = "place";
      this.showRoute = false;
    },
    keepSelectionVisible() {
      if (
        !this.filteredBuildings.some(
          (building) => building.id === this.selectedId
        )
      ) {
        this.selectedId = this.filteredBuildings.length
          ? this.filteredBuildings[0].id
          : "";
      }
    },
    clearFilters() {
      this.searchQuery = "";
      this.activeCategory = "";
    },
    prepareDirections(destinationId) {
      this.originId = "42";
      this.destinationId = destinationId;
      this.activeTab = "directions";
      this.showRoute = true;
    },
    swapPlaces() {
      const currentOrigin = this.originId;
      this.originId = this.destinationId;
      this.destinationId = currentOrigin;
    },
    zoomMap(direction) {
      this.mapZoom = Math.min(
        1.35,
        Math.max(0.85, this.mapZoom + direction * 0.1)
      );
    },
    formatDistance(distance) {
      return distance < 1000
        ? `${distance} m`
        : `${(distance / 1000).toFixed(1)} km`;
    },
    estimateMinutes(distance) {
      return Math.max(1, Math.round(distance / 80));
    },
  },
};
</script>

<style lang="scss" scoped>
.campus-app {
  min-height: 100vh;
  background: radial-gradient(
      ellipse at 86% 13%,
      rgba(232, 237, 224, 0.55),
      transparent 28rem
    ),
    #f5f6f1;
}

.topbar {
  height: 74px;
  padding: 0 clamp(20px, 5vw, 78px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid #e8ebe4;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #233b30;
  text-decoration: none;
}

.brand-mark {
  width: 35px;
  height: 35px;
  display: grid;
  place-items: center;
  background: #e8f0e7;
  border-radius: 11px;

  svg {
    width: 23px;
    fill: none;
    stroke: #39684e;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
}

.brand-name {
  font-family: "Manrope", "Segoe UI", "Microsoft JhengHei", sans-serif;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.5px;

  span {
    color: #65816e;
    font-weight: 600;
  }
}

.top-nav {
  display: flex;
  align-items: center;
  gap: clamp(20px, 3.2vw, 48px);
  height: 100%;
}

.nav-link {
  position: relative;
  height: 100%;
  display: grid;
  align-items: center;
  color: #758078;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s ease;

  &:hover,
  &.active {
    color: #315d46;
  }

  &.active::after {
    position: absolute;
    right: 0;
    bottom: -1px;
    left: 0;
    height: 2px;
    background: #528264;
    content: "";
  }
}

.campus-link {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 13px;
  color: #3a604a;
  border: 1px solid #dfe8df;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  text-decoration: none;

  &:hover {
    background: #f0f5ef;
  }
}

main {
  max-width: 1600px;
  margin: 0 auto;
  padding: 37px clamp(20px, 5vw, 78px) 25px;
}

.intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 25px;
}

.eyebrow,
.section-kicker {
  color: #74857a;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.45px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
}

.eyebrow-dot {
  width: 6px;
  height: 6px;
  background: #588063;
  border-radius: 50%;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  margin: 11px 0 6px;
  color: #27392f;
  font-family: "Manrope", "Segoe UI", "Microsoft JhengHei", sans-serif;
  font-size: clamp(28px, 3.2vw, 43px);
  font-weight: 700;
  letter-spacing: -2px;
  line-height: 1.14;

  span {
    color: #76917b;
    font-weight: 500;
  }
}

.intro > div:first-child > p {
  margin-bottom: 0;
  color: #89918a;
  font-size: 12px;
}

.campus-note {
  display: flex;
  align-items: center;
  gap: 11px;
  margin: 0 10px 4px 20px;

  > span:last-child {
    display: grid;
    gap: 3px;
  }

  strong {
    color: #4a6251;
    font-size: 11px;
  }

  small {
    color: #929a92;
    font-size: 10px;
  }
}

.note-icon {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #64826b;
  background: #e8eee4;
  border-radius: 50%;
  font-size: 18px;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(235px, 0.79fr) minmax(430px, 1.85fr) minmax(
      255px,
      0.91fr
    );
  gap: 14px;
  align-items: stretch;
}

.panel {
  min-width: 0;
  background: #fff;
  border: 1px solid #e9ece6;
  border-radius: 13px;
  box-shadow: 0 8px 26px rgba(40, 62, 46, 0.035);
}

.directory {
  display: flex;
  flex-direction: column;
  min-height: 573px;
  padding: 19px 15px 0;
}

.panel-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.directory-heading {
  margin: 1px 2px 15px;

  h2 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 6px 0 0;
    color: #2f4035;
    font-family: "Manrope", "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 16px;
    letter-spacing: -0.55px;
  }
}

.place-count {
  min-width: 20px;
  height: 19px;
  display: grid;
  place-items: center;
  padding: 0 5px;
  color: #68816d;
  background: #edf2eb;
  border-radius: 7px;
  font: 700 9px "DM Sans", sans-serif;
}

.clear-button {
  padding: 4px 0;
  color: #63816b;
  background: none;
  border: 0;
  font-size: 10px;
  font-weight: 700;
}

.search-box {
  height: 37px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 10px;
  border: 1px solid #e9ece6;
  border-radius: 7px;
  background: #fbfcfa;

  svg {
    width: 15px;
    flex: none;
    fill: none;
    stroke: #89968c;
    stroke-width: 1.6;
    stroke-linecap: round;
  }

  input {
    width: 100%;
    min-width: 0;
    padding: 0;
    color: #37473d;
    background: transparent;
    border: 0;
    outline: none;
    font-size: 10px;

    &::placeholder {
      color: #a0a8a0;
    }

    &::-webkit-search-cancel-button {
      cursor: pointer;
    }
  }

  kbd {
    min-width: 17px;
    padding: 2px 4px;
    color: #9ca39c;
    background: #f1f3ef;
    border: 1px solid #e9ece6;
    border-radius: 4px;
    font: 9px "DM Sans", sans-serif;
    text-align: center;
  }
}

.category-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0 15px;
}

.filter-chip {
  min-height: 25px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 8px;
  color: #7d887f;
  background: #fff;
  border: 1px solid #e9ece6;
  border-radius: 20px;
  font-size: 9px;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.18s, border-color 0.18s, color 0.18s;

  &:hover {
    border-color: #b7c8b7;
  }

  &.chosen {
    color: #41654d;
    background: #edf3eb;
    border-color: #dce8da;
  }
}

.chip-dot {
  width: 6px;
  height: 6px;
  background: var(--chip-color);
  border-radius: 50%;
}

.list-caption {
  display: flex;
  justify-content: space-between;
  padding: 0 3px 8px;
  color: #a0a9a0;
  border-bottom: 1px solid #eff1ed;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1.05px;

  span:last-child {
    font-weight: 500;
    letter-spacing: 0;
  }
}

.place-list {
  flex: 1;
  overflow: auto;
  scrollbar-color: #dce5db transparent;
  scrollbar-width: thin;
}

.place-row {
  width: 100%;
  min-height: 54px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 4px;
  color: inherit;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #f0f2ee;
  border-radius: 0;
  text-align: left;
  transition: background 0.15s;

  &:hover,
  &.selected {
    background: #f7f9f5;
  }

  &.selected {
    box-shadow: inset 2px 0 #709174;
  }
}

.place-symbol {
  width: 28px;
  height: 28px;
  flex: none;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--category-color);
  border-radius: 9px;
  font-size: 10px;
  font-weight: 700;
}

.place-copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 3px;

  strong {
    overflow: hidden;
    color: #45554a;
    font-size: 10px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  small {
    color: #9aa39b;
    font-size: 9px;
  }
}

.row-arrow {
  color: #a9b1a9;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.15s;

  .place-row:hover &,
  .place-row.selected & {
    opacity: 1;
  }
}

.empty-state {
  padding: 32px 10px;
  color: #7d8a80;
  text-align: center;

  > span {
    display: block;
    margin-bottom: 8px;
    font-size: 22px;
  }

  strong {
    display: block;
    color: #536458;
    font-size: 11px;
  }

  p {
    margin: 5px 0 12px;
    font-size: 10px;
    line-height: 1.5;
  }

  button {
    padding: 6px 10px;
    color: #44674f;
    background: #edf3eb;
    border: 0;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 700;
  }
}

.directory-footer {
  min-height: 54px;
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 -15px;
  padding: 8px 16px;
  background: #fbfcfa;
  border-top: 1px solid #eff1ed;
  border-radius: 0 0 13px 13px;

  > span:last-child {
    display: grid;
    gap: 3px;
  }

  strong {
    color: #718075;
    font-size: 9px;
  }

  small {
    color: #a0a8a0;
    font-size: 8px;
  }
}

.footer-pin {
  width: 25px;
  height: 25px;
  display: grid;
  place-items: center;
  color: #62816a;
  background: #eaf0e8;
  border-radius: 8px;
  font-size: 16px;
}

.map-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-toolbar {
  min-height: 57px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 17px;
  border-bottom: 1px solid #eff1ed;
}

.map-title {
  display: flex;
  align-items: center;
  gap: 9px;

  > span:last-child {
    display: grid;
    gap: 3px;
  }

  strong {
    color: #435448;
    font-size: 10px;
    font-weight: 700;
  }

  small {
    color: #9ba49c;
    font-size: 9px;
  }
}

.map-live-dot,
.map-status i {
  width: 7px;
  height: 7px;
  background: #6a9372;
  border-radius: 50%;
}

.map-live-dot {
  box-shadow: 0 0 0 4px #eff4ed;
}

.map-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.map-scale {
  margin-right: 7px;
  color: #a0a8a0;
  font-size: 9px;
}

.icon-button {
  width: 27px;
  height: 27px;
  display: grid;
  place-items: center;
  padding: 0;
  color: #748277;
  background: #fff;
  border: 1px solid #e9ece6;
  border-radius: 6px;
  font-size: 16px;

  &:hover {
    color: #3d654a;
    background: #f3f6f1;
  }

  svg {
    width: 13px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
}

.map-canvas {
  position: relative;
  min-height: 0;
  flex: 1;
  overflow: hidden;
  background-color: #f1f3e8;
  background-image: radial-gradient(
    rgba(138, 157, 127, 0.2) 0.7px,
    transparent 0.7px
  );
  background-size: 12px 12px;
}

.campus-map {
  width: 100%;
  height: 100%;
  display: block;
}

.campus-ground {
  fill: #d9e7ce;
  stroke: #a8bca0;
  stroke-width: 16;
  stroke-linejoin: round;
  filter: drop-shadow(0 13px 10px rgba(48, 62, 47, 0.17));
}

.campus-boundary {
  fill: none;
  stroke: #f5f2e7;
  stroke-width: 3;
  stroke-dasharray: 4 7;
  stroke-linejoin: round;
}

.landscape-grove {
  fill: #b6d0a8;
}
.landscape-field {
  fill: #c4daa7;
}
.landscape-lake {
  fill: #91bdca;
  stroke: #e0f1ed;
  stroke-width: 8;
}
.lake-shine {
  fill: none;
  stroke: #c9e4e6;
  stroke-width: 5;
  stroke-linecap: round;
}
.athletic-track {
  fill: #c88872;
  stroke: #e3ae98;
  stroke-width: 7;
}
.athletic-field {
  fill: #91bb86;
  stroke: #f3e6cb;
  stroke-width: 3;
}
.sports-court {
  fill: #83b0a0;
  stroke: #f4eee1;
  stroke-width: 3;
}
.landscape-labels text {
  fill: #53725d;
  font-family: "Microsoft JhengHei", sans-serif;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 2px;
  text-anchor: middle;
  paint-order: stroke;
  stroke: #e1ecd8;
  stroke-width: 5;
  pointer-events: none;
}

.campus-road-bed,
.campus-walkway {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.campus-road-bed {
  stroke: #b8bbad;
  stroke-width: 29;
}

.campus-walkway {
  stroke: #f6f0dc;
  stroke-width: 21;
}

.map-north,
.map-edge-label {
  fill: #71856f;
  font-family: "Microsoft JhengHei", sans-serif;
  font-size: 15px;
  font-weight: 700;
}

.north-arrow {
  fill: none;
  stroke: #71856f;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.isometric-building {
  cursor: pointer;
  transform-box: fill-box;
  transform-origin: center bottom;
  transition: filter 0.16s ease;

  .building-shadow {
    fill: rgba(57, 68, 51, 0.15);
    transform: translate(4px, 5px);
  }

  .building-left-face {
    fill: var(--building-color);
    filter: brightness(0.69);
    stroke: rgba(62, 69, 53, 0.26);
    stroke-width: 1;
  }

  .building-right-face {
    fill: var(--building-color);
    filter: brightness(0.84);
    stroke: rgba(62, 69, 53, 0.26);
    stroke-width: 1;
  }

  .building-roof {
    fill: var(--building-color);
    stroke: rgba(255, 255, 255, 0.76);
    stroke-width: 1.4;
    stroke-linejoin: round;
  }

  .building-detail {
    fill: none;
    stroke: rgba(255, 255, 255, 0.82);
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    pointer-events: none;
  }

  .building-roof-accent {
    fill: var(--building-color);
    filter: brightness(1.2);
    stroke: rgba(255, 255, 255, 0.8);
    stroke-width: 1;
    pointer-events: none;
  }

  .courtyard-opening {
    filter: brightness(0.58);
  }

  .building-gate {
    fill: none;
    stroke: var(--building-color);
    stroke-width: 5;
    stroke-linecap: round;
    stroke-linejoin: round;
    pointer-events: none;
  }

  .building-windows {
    fill: none;
    stroke: rgba(255, 255, 255, 0.78);
    stroke-width: 1.5;
    pointer-events: none;
  }

  .building-number {
    fill: #fff;
    font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    font-size: 8px;
    font-weight: 800;
    paint-order: stroke;
    stroke: rgba(53, 62, 48, 0.42);
    stroke-width: 2px;
    stroke-linejoin: round;
    text-anchor: middle;
    pointer-events: none;
  }

  &:hover,
  &.selected,
  &:focus-visible {
    filter: drop-shadow(0 5px 4px rgba(43, 62, 44, 0.3));
  }

  &.selected .building-roof,
  &:focus-visible .building-roof {
    stroke: #fff;
    stroke-width: 3;
  }

  &.route-stop .building-roof {
    stroke: #d27e4b;
    stroke-width: 3;
  }

  &:focus-visible {
    outline: none;
  }
}

.route-line {
  fill: none;
  stroke: #d27e4b;
  stroke-width: 7;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 9 5;
  opacity: 0.95;
  filter: drop-shadow(0 1px 2px rgba(92, 75, 58, 0.18));

  &.accessible {
    stroke: #397c64;
  }
}

.route-endpoints circle {
  stroke: white;
  stroke-width: 4;
}

.route-start {
  fill: #557a62;
}

.route-end {
  fill: #d27e4b;
}

.map-legend {
  position: absolute;
  bottom: 17px;
  left: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 7px 12px;
  max-width: 72%;
  padding: 9px 11px;
  background: rgba(255, 255, 255, 0.93);
  border: 1px solid rgba(226, 231, 220, 0.9);
  border-radius: 8px;
  box-shadow: 0 3px 12px rgba(61, 76, 59, 0.06);

  span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: #78857a;
    font-size: 8px;
    font-weight: 600;
    white-space: nowrap;
  }

  i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }
}

.route-map-badge {
  position: absolute;
  top: 13px;
  left: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  color: #55745d;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #e5eadd;
  border-radius: 6px;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.route-dot {
  width: 7px;
  height: 7px;
  background: #d27e4b;
  border-radius: 50%;
}

.map-attribution {
  position: absolute;
  right: 10px;
  bottom: 10px;
  color: #899485;
  font-size: 8px;
}

.map-bottom {
  min-height: 37px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 14px;
  color: #9aa29a;
  border-top: 1px solid #eff1ed;
  font-size: 8px;

  > span:first-child {
    display: flex;
    align-items: center;
    gap: 5px;
  }
}

.map-hint-icon {
  color: #77937b;
  font-size: 13px;
}

.map-status {
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;

  i {
    width: 5px;
    height: 5px;
  }
}

.details-panel {
  display: flex;
  flex-direction: column;
  min-height: 573px;
  overflow: hidden;
}

.detail-tabs {
  min-height: 51px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 0 13px;
  border-bottom: 1px solid #eff1ed;

  button {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 0 4px;
    color: #98a198;
    background: none;
    border: 0;
    font-size: 9px;
    font-weight: 600;

    &.active {
      color: #44684e;
    }

    &.active::after {
      position: absolute;
      right: 6px;
      bottom: -1px;
      left: 6px;
      height: 2px;
      background: #63916a;
      content: "";
    }
  }

  svg {
    width: 13px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.4;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
}

.detail-content {
  flex: 1;
  padding: 20px 17px 14px;
}

.detail-category {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8d988f;
  font-size: 9px;
  font-weight: 600;
}

.detail-category-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.detail-id {
  margin-left: auto;
  color: #b2b9b1;
  font-size: 7px;
  letter-spacing: 0.9px;
}

.selected-place h2,
.directions-content h2 {
  margin: 10px 0 7px;
  color: #2f4035;
  font-family: "Manrope", "Segoe UI", "Microsoft JhengHei", sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.8px;
  line-height: 1.2;
}

.place-description {
  margin: 0;
  color: #89938b;
  font-size: 10px;
  line-height: 1.65;
}

.detail-divider {
  height: 1px;
  margin: 18px 0 15px;
  background: #edf0eb;
}

.info-heading {
  display: flex;
  align-items: center;
  gap: 7px;

  strong {
    color: #55665a;
    font-size: 10px;
  }
}

.info-icon {
  color: #709174;
  font-size: 15px;
}

.info-body {
  margin: 6px 0 13px 21px;
  color: #929b93;
  font-size: 9px;
  line-height: 1.55;
}

.access-card {
  display: flex;
  gap: 9px;
  padding: 11px 10px;
  background: #f6f8f3;
  border: 1px solid #ebefe7;
  border-radius: 8px;

  > div {
    min-width: 0;
  }

  strong {
    display: block;
    color: #637467;
    font-size: 9px;
  }

  p {
    margin: 4px 0 6px;
    color: #8f9990;
    font-size: 8px;
    line-height: 1.55;
  }
}

.access-icon {
  color: #739078;
  font-size: 14px;
}

.unverified-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #9b835e;
  font-size: 7px;

  i {
    width: 5px;
    height: 5px;
    background: #c29a61;
    border-radius: 50%;
  }
}

.detail-spacer {
  min-height: 12px;
  flex: 1;
}

.primary-button {
  width: 100%;
  min-height: 39px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 0 12px;
  color: #fff;
  background: #416b50;
  border: 1px solid #416b50;
  border-radius: 7px;
  box-shadow: 0 3px 7px rgba(54, 91, 64, 0.12);
  font-size: 10px;
  font-weight: 700;
  transition: background 0.18s, transform 0.18s;

  &:hover {
    background: #345b43;
    transform: translateY(-1px);
  }

  svg {
    width: 15px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.4;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  span {
    margin-left: auto;
    font-size: 14px;
  }
}

.data-note {
  margin: 9px 0 0;
  color: #a0a8a0;
  font-size: 7px;
  line-height: 1.5;
  text-align: center;
}

.detail-foot {
  min-height: 39px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 12px;
  color: #a2aaa2;
  background: #fbfcfa;
  border-top: 1px solid #eff1ed;
  font-size: 7px;
  letter-spacing: 0.65px;

  span:last-child {
    font-size: 7px;
    letter-spacing: 0;
    text-align: right;
  }

  i {
    color: #6c8b72;
    font-size: 10px;
    font-style: normal;
  }
}

.directions-content {
  padding-top: 19px;

  h2 {
    margin-top: 8px;
    font-size: 19px;
  }
}

.directions-intro {
  margin: 0 0 17px;
  color: #8f9990;
  font-size: 9px;
}

.select-label {
  display: block;
  margin-bottom: 6px;
  color: #89958b;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.75px;
}

.select-wrap {
  position: relative;
  display: flex;
  align-items: center;

  select {
    width: 100%;
    height: 36px;
    padding: 0 26px 0 28px;
    color: #526257;
    background: #fbfcfa;
    border: 1px solid #e6ebe3;
    border-radius: 7px;
    appearance: none;
    font-size: 9px;
  }

  &::after {
    position: absolute;
    right: 11px;
    color: #8b988d;
    content: "⌄";
    pointer-events: none;
  }
}

.select-marker {
  position: absolute;
  z-index: 1;
  left: 11px;
  width: 8px;
  height: 8px;
  border: 2px solid #65846b;
  border-radius: 50%;
  pointer-events: none;
}

.destination-marker {
  border-color: #c77c52;
}

.swap-button {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  margin: -1px 0 -1px 9px;
  color: #718575;
  background: #fff;
  border: 1px solid #e6ebe3;
  border-radius: 6px;
  font-size: 13px;
}

.accessible-toggle {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 14px 0 13px;
  cursor: pointer;

  input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;

    &:focus-visible + .toggle-ui {
      outline: 3px solid #e29b54;
      outline-offset: 3px;
    }

    &:checked + .toggle-ui {
      background: #5d8567;
    }

    &:checked + .toggle-ui::after {
      transform: translateX(12px);
    }
  }

  > span:last-child {
    display: grid;
    gap: 3px;
  }

  strong {
    color: #56685a;
    font-size: 9px;
  }

  small {
    color: #9aa39b;
    font-size: 8px;
  }
}

.toggle-ui {
  width: 29px;
  height: 17px;
  flex: none;
  position: relative;
  background: #cdd5cc;
  border-radius: 12px;
  transition: background 0.18s;

  &::after {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 11px;
    height: 11px;
    background: #fff;
    border-radius: 50%;
    content: "";
    transition: transform 0.18s;
  }
}

.route-button {
  min-height: 36px;
  font-size: 9px;
}

.route-result {
  margin-top: 13px;
  padding: 10px;
  background: #f6f8f4;
  border: 1px solid #e9eee6;
  border-radius: 8px;
}

.route-result-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 9px;
  border-bottom: 1px solid #e8ede4;

  > span:last-child {
    display: grid;
    gap: 3px;
  }

  strong {
    color: #4c6852;
    font-size: 9px;
  }

  small {
    color: #8e9a90;
    font-size: 8px;
  }
}

.route-check {
  width: 21px;
  height: 21px;
  display: grid;
  place-items: center;
  color: #467452;
  background: #e3eee2;
  border-radius: 50%;
  font-size: 11px;
}

.route-steps {
  padding: 7px 0 1px 3px;
}

.route-step {
  position: relative;
  min-height: 36px;
  display: flex;
  align-items: center;
  gap: 9px;

  &:not(:last-child)::after {
    position: absolute;
    top: 23px;
    bottom: -3px;
    left: 4px;
    border-left: 1px dashed #b6c8b4;
    content: "";
  }

  > span:last-child {
    display: grid;
    gap: 2px;
  }

  small {
    color: #98a49a;
    font-size: 6px;
    font-weight: 700;
    letter-spacing: 0.7px;
  }

  strong {
    color: #5d6e61;
    font-size: 8px;
    font-weight: 600;
  }
}

.step-marker {
  z-index: 1;
  width: 9px;
  height: 9px;
  flex: none;
  background: #61836a;
  border: 2px solid #f6f8f4;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #91ad91;

  &.last {
    background: #cc8055;
    box-shadow: 0 0 0 1px #dca07c;
  }
}

.route-disclaimer {
  margin: 6px 0 0;
  color: #9da69e;
  font-size: 7px;
  line-height: 1.5;
}

.route-unavailable {
  display: flex;
  gap: 8px;
  margin-top: 13px;
  padding: 10px;
  color: #866c4c;
  background: #fbf7f0;
  border: 1px solid #f0e7d8;
  border-radius: 8px;

  > span {
    width: 17px;
    height: 17px;
    flex: none;
    display: grid;
    place-items: center;
    color: #8d714c;
    background: #f2e9da;
    border-radius: 50%;
    font-size: 10px;
    font-weight: 700;
  }

  strong {
    display: block;
    margin: 1px 0 4px;
    font-size: 9px;
  }

  p {
    margin: 0;
    color: #998a75;
    font-size: 8px;
    line-height: 1.5;
  }
}

.route-tip {
  display: flex;
  gap: 8px;
  margin-top: 13px;
  padding: 10px;
  color: #708273;
  background: #f5f8f3;
  border: 1px solid #ebefe8;
  border-radius: 7px;

  > span {
    color: #7a9a7d;
    font-size: 11px;
  }

  p {
    margin: 0;
    font-size: 8px;
    line-height: 1.55;
  }
}

.map-disclaimer {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-top: 14px;
  padding: 11px 14px;
  background: #f0f3eb;
  border: 1px solid #e5ebe0;
  border-radius: 9px;

  p {
    flex: 1;
    margin: 0;
    color: #859186;
    font-size: 8px;
    line-height: 1.55;
  }

  strong {
    margin-right: 3px;
    color: #5b6d5e;
    font-size: 9px;
  }
}

.disclaimer-symbol {
  width: 21px;
  height: 21px;
  flex: none;
  display: grid;
  place-items: center;
  color: #6e896f;
  background: #e1eade;
  border-radius: 50%;
  font-family: Georgia, serif;
  font-size: 12px;
  font-style: italic;
}

.disclaimer-tag {
  padding: 5px 7px;
  color: #8d9a8d;
  background: #e8eee5;
  border-radius: 4px;
  font-size: 7px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.site-footer {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 2px;
  padding: 0 clamp(20px, 5vw, 78px);
  color: #a0a8a0;
  border-top: 1px solid #e9ece6;
  font-size: 8px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  clip-path: inset(50%);
}

@media (min-width: 1450px) {
  .workspace {
    grid-template-columns: minmax(250px, 0.78fr) minmax(550px, 1.85fr) minmax(
        290px,
        0.91fr
      );
  }

  .directory,
  .details-panel {
    min-height: 650px;
  }
}

@media (max-width: 1160px) {
  main {
    padding-right: 28px;
    padding-left: 28px;
  }

  .workspace {
    grid-template-columns: minmax(220px, 0.75fr) minmax(390px, 1.6fr);
  }

  .details-panel {
    grid-column: 1 / -1;
    min-height: initial;
  }

  .detail-content {
    min-height: 300px;
  }

  .selected-place {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 22px;
  }

  .selected-place .detail-category,
  .selected-place h2,
  .selected-place .place-description,
  .selected-place .detail-divider,
  .selected-place .detail-spacer,
  .selected-place .primary-button,
  .selected-place .data-note {
    grid-column: 1 / -1;
  }

  .selected-place .detail-divider {
    margin: 12px 0;
  }

  .selected-place .access-card {
    align-self: start;
  }

  .directions-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 15px;
  }

  .directions-content > .section-kicker,
  .directions-content > h2,
  .directions-content > .directions-intro,
  .directions-content > .accessible-toggle,
  .directions-content > .route-button,
  .directions-content > .route-result,
  .directions-content > .route-unavailable,
  .directions-content > .route-tip,
  .directions-content > .detail-spacer,
  .directions-content > .data-note {
    grid-column: 1 / -1;
  }

  .directions-content > .select-label:nth-of-type(2) {
    grid-column: 1;
  }
}

@media (max-width: 760px) {
  .topbar {
    height: 62px;
    padding: 0 18px;
  }

  .top-nav {
    gap: 16px;
  }

  .nav-link {
    font-size: 10px;
  }

  .top-nav a:last-child,
  .campus-link {
    display: none;
  }

  main {
    padding: 25px 18px 19px;
  }

  .intro {
    align-items: flex-start;
    margin-bottom: 19px;
  }

  h1 {
    font-size: 32px;
    letter-spacing: -1.5px;
  }

  .intro > div:first-child > p {
    max-width: 390px;
    font-size: 11px;
    line-height: 1.55;
  }

  .campus-note {
    display: none;
  }

  .workspace {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .map-panel {
    grid-row: 1;
    min-height: 390px;
  }

  .map-canvas {
    min-height: 320px;
  }

  .directory {
    grid-row: 2;
    min-height: 0;
    padding-bottom: 0;
  }

  .place-list {
    max-height: 285px;
    overflow: auto;
  }

  .details-panel {
    grid-row: 3;
  }

  .detail-content {
    min-height: 0;
  }

  .selected-place {
    display: block;
  }

  .selected-place .detail-divider {
    margin: 16px 0 13px;
  }

  .selected-place .access-card {
    margin-bottom: 12px;
  }

  .selected-place .detail-spacer {
    min-height: 12px;
  }

  .directions-content {
    display: block;
  }

  .map-disclaimer {
    align-items: flex-start;
    padding: 10px;
  }

  .disclaimer-tag {
    display: none;
  }

  .site-footer {
    padding: 0 18px;
    font-size: 7px;
  }
}

@media (max-width: 420px) {
  .topbar {
    padding: 0 14px;
  }

  .brand-name {
    font-size: 13px;
  }

  .top-nav {
    gap: 12px;
  }

  main {
    padding-right: 12px;
    padding-left: 12px;
  }

  h1 {
    font-size: 29px;
  }

  .map-panel {
    min-height: 340px;
  }

  .map-canvas {
    min-height: 273px;
  }

  .map-toolbar {
    padding: 0 11px;
  }

  .map-scale {
    display: none;
  }

  .map-legend {
    max-width: calc(100% - 25px);
    gap: 6px 9px;
    padding: 7px 8px;
  }

  .map-legend span {
    font-size: 7px;
  }

  .map-bottom {
    padding: 0 9px;
    font-size: 7px;
  }

  .map-status {
    font-size: 0;
  }

  .map-status i {
    width: 6px;
    height: 6px;
  }

  .site-footer span:last-child {
    max-width: 150px;
    text-align: right;
  }
}
</style>
