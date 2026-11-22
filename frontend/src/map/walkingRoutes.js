const radians = Math.PI / 180;
const maxEndpointDistance = 120;
const footHighways = new Set([
  "footway",
  "pedestrian",
  "steps",
  "path",
  "track",
  "service",
  "residential",
  "living_street",
  "unclassified",
  "tertiary",
  "secondary",
  "primary",
]);
const allowedFoot = new Set(["yes", "designated", "permissive", "official"]);
const restricted = new Set([
  "no",
  "private",
  "customers",
  "permit",
  "destination",
]);
const barriers = new Set([
  "cycle_barrier",
  "stile",
  "turnstile",
  "chain",
  "kissing_gate",
  "block",
  "gate",
  "lift_gate",
]);

export function distanceMeters(a, b) {
  const latitude = ((a[1] + b[1]) / 2) * radians;
  const dx = (b[0] - a[0]) * Math.cos(latitude);
  return 6371008.8 * radians * Math.hypot(dx, b[1] - a[1]);
}

function permitsFoot(tags) {
  return (
    allowedFoot.has(tags.foot) ||
    (!restricted.has(tags.foot) && !restricted.has(tags.access))
  );
}

function blocksWheelchair(tags) {
  const incline =
    typeof tags.incline === "string" && tags.incline.endsWith("%")
      ? Number.parseFloat(tags.incline)
      : 0;
  return (
    tags.wheelchair === "no" ||
    tags.highway === "steps" ||
    tags.kerb === "raised" ||
    Math.abs(incline) > 8.33 ||
    ["bad", "very_bad", "horrible", "very_horrible", "impassable"].includes(
      tags.smoothness
    ) ||
    (barriers.has(tags.barrier) && tags.wheelchair !== "yes")
  );
}

function projectOnSegment(point, a, b) {
  const scale = Math.cos(point[1] * radians);
  const dx = (b[0] - a[0]) * scale;
  const dy = b[1] - a[1];
  const length = dx * dx + dy * dy;
  const offset = length
    ? ((point[0] - a[0]) * scale * dx + (point[1] - a[1]) * dy) / length
    : 0;
  const position = Math.max(0, Math.min(1, offset));
  return [a[0] + position * (b[0] - a[0]), a[1] + position * (b[1] - a[1])];
}

function createSegments(network) {
  const segments = [];
  for (const { nodes, id, tags } of network.ways) {
    if (
      !permitsFoot(tags) ||
      (!footHighways.has(tags.highway) && !allowedFoot.has(tags.foot))
    )
      continue;
    for (let index = 1; index < nodes.length; index += 1) {
      const from = nodes[index - 1];
      const to = nodes[index];
      const a = network.nodes[from];
      const b = network.nodes[to];
      const meters = distanceMeters(a, b);
      if (meters && permitsFoot(a[2]) && permitsFoot(b[2])) {
        segments.push({
          from,
          to,
          a,
          b,
          meters,
          tags,
          key: [from, to].sort().join(":"),
          way: id,
        });
      }
    }
  }
  return segments;
}

export function createRoutePlanner(network) {
  const segments = createSegments(network);

  function nearestSegment(point) {
    let nearest = null;
    let minimum = 15;
    for (const segment of segments) {
      const closest = projectOnSegment(point, segment.a, segment.b);
      const meters = distanceMeters(point, closest);
      if (meters < minimum) {
        minimum = meters;
        nearest = segment;
      }
    }
    return nearest;
  }

  function roadClosures(reports) {
    return new Set(
      reports
        .filter(
          (report) => report.kind === "construction" && report.road_closed
        )
        .map(
          (report) => nearestSegment([report.longitude, report.latitude])?.key
        )
        .filter(Boolean)
    );
  }

  return {
    nearestRoad(point) {
      return nearestSegment(point)?.way ?? null;
    },
    plan(start, end, mode, reports) {
      const blocked = roadClosures(reports);
      const available = segments.filter(
        (segment) =>
          !blocked.has(segment.key) &&
          (mode !== "wheelchair" ||
            ![segment.tags, segment.a[2], segment.b[2]].some(blocksWheelchair))
      );
      const neighbors = buildGraph(available);
      const components = connectedComponents(neighbors);
      const fromOptions = endpointCandidates(start, available, components);
      const toOptions = endpointCandidates(end, available, components);
      let best = null;
      for (const [component, starts] of fromOptions) {
        const ends = toOptions.get(component);
        if (!ends) continue;
        for (const from of starts) {
          for (const to of ends) {
            if (distanceMeters(from.coordinates, to.coordinates) < 0.1) continue;
            const graph = new Map(
              [...neighbors].map(([node, edges]) => [node, [...edges]])
            );
            attachEndpoint(graph, "start", from);
            attachEndpoint(graph, "end", to);
            if (from.segment.key === to.segment.key) {
              connect(graph, "start", "end", {
                ...from.segment,
                meters: distanceMeters(from.coordinates, to.coordinates),
              });
            }
            const route = shortestPath(graph, "start", "end", mode);
            if (!route) continue;
            const cost =
              from.offset +
              to.offset +
              route.reduce((sum, edge) => sum + edgeWeight(edge, mode), 0);
            if (!best || cost < best.cost)
              best = { from, to, fullPath: route, cost };
          }
        }
      }
      if (!best) return null;
      const { from, to, fullPath } = best;
      const path = fullPath.filter(({ meters }) => meters > 0.0001);
      const coverage = { distance: 0, lit: 0, lightingKnown: 0, wheelchair: 0 };
      for (const { meters, tags } of path) {
        coverage.distance += meters;
        if (tags.lit === "yes") coverage.lit += meters;
        if (["yes", "no"].includes(tags.lit)) coverage.lightingKnown += meters;
        if (tags.wheelchair === "yes") coverage.wheelchair += meters;
      }
      // All projected endpoints and intermediate nodes follow original OSM edges.
      const pointFor = (id) =>
        id === "start"
          ? from.coordinates
          : id === "end"
          ? to.coordinates
          : network.nodes[id];
      const coordinates = [
        from.coordinates,
        ...path.map(({ node }) => pointFor(node)),
      ].map(([lon, lat]) => [lon, lat]);
      return {
        ...coverage,
        coordinates,
        startOffset: from.offset,
        endOffset: to.offset,
        osmWayIds: path.map(({ way }) => way),
      };
    },
  };
}

function buildGraph(segments) {
  const graph = new Map();
  for (const segment of segments) {
    connect(graph, segment.from, segment.to, segment);
  }
  return graph;
}

function connect(graph, from, to, segment) {
  if (!graph.has(from)) graph.set(from, []);
  if (!graph.has(to)) graph.set(to, []);
  const edge = { meters: segment.meters, tags: segment.tags, way: segment.way };
  graph.get(from).push({ ...edge, node: to });
  graph.get(to).push({ ...edge, node: from });
}

function connectedComponents(graph) {
  const components = new Map();
  for (const node of graph.keys()) {
    if (components.has(node)) continue;
    const pending = [node];
    components.set(node, node);
    for (let index = 0; index < pending.length; index += 1) {
      for (const edge of graph.get(pending[index])) {
        if (components.has(edge.node)) continue;
        components.set(edge.node, node);
        pending.push(edge.node);
      }
    }
  }
  return components;
}

function endpointCandidates(point, segments, components) {
  const candidates = new Map();
  let closest = Infinity;
  for (const segment of segments) {
    const coordinates = projectOnSegment(point, segment.a, segment.b);
    const offset = distanceMeters(point, coordinates);
    if (offset > maxEndpointDistance) continue;
    closest = Math.min(closest, offset);
    const component = components.get(segment.from);
    if (!candidates.has(component)) candidates.set(component, []);
    candidates.get(component).push({ segment, coordinates, offset });
  }
  // Exact road points stay on their component. Building reference points may
  // select another nearby road, with the remaining offset shown to the user.
  const limit = closest <= 1 ? 1 : closest + 35;
  return new Map(
    [...candidates]
      .map(([component, options]) => [
        component,
        options.filter((candidate) => candidate.offset <= limit),
      ])
      .filter(([, options]) => options.length)
  );
}

function attachEndpoint(graph, id, { segment, coordinates }) {
  connect(graph, id, segment.from, {
    ...segment,
    meters: distanceMeters(coordinates, segment.a),
  });
  connect(graph, id, segment.to, {
    ...segment,
    meters: distanceMeters(coordinates, segment.b),
  });
}

export function walkingNetworkGeoJSON(network) {
  return {
    type: "FeatureCollection",
    features: network.ways.map((way) => ({
      type: "Feature",
      properties: {
        ...way.tags,
        id: "way/" + way.id,
        osm_url: "https://www.openstreetmap.org/way/" + way.id,
        data_source: "OpenStreetMap contributors",
      },
      geometry: {
        type: "LineString",
        coordinates: way.nodes.map((id) => network.nodes[id].slice(0, 2)),
      },
    })),
  };
}

function edgeWeight(edge, mode) {
  if (mode === "night") {
    if (edge.tags.lit === "yes") return edge.meters;
    return edge.meters * (edge.tags.lit === "no" ? 4 : 2);
  }
  if (mode === "wheelchair" && edge.tags.wheelchair !== "yes")
    return edge.meters * 1.5;
  return edge.meters;
}

function shortestPath(graph, start, destination, mode) {
  // The campus extract is small enough to scan the frontier without a heap dependency.
  const frontier = new Map([[start, 0]]);
  const costs = new Map(frontier);
  const previous = new Map();
  while (frontier.size) {
    let current;
    let cheapest = Infinity;
    for (const [node, weight] of frontier) {
      if (weight < cheapest) {
        current = node;
        cheapest = weight;
      }
    }
    if (current === destination) {
      const path = [];
      for (let node = destination; node !== start; ) {
        const step = previous.get(node);
        path.push(step.edge);
        node = step.from;
      }
      return path.reverse();
    }
    frontier.delete(current);
    for (const edge of graph.get(current)) {
      const cost = cheapest + edgeWeight(edge, mode);
      if (cost >= (costs.get(edge.node) ?? Infinity)) continue;
      costs.set(edge.node, cost);
      frontier.set(edge.node, cost);
      previous.set(edge.node, { from: current, edge });
    }
  }
  return null;
}
