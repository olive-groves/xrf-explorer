<script setup lang="ts">
import { ref } from 'vue';
import { Window } from '@/components/ui/window';
import { watch } from 'vue';
import * as d3 from 'd3';

// const url = 'http://localhost:8001';

const chart = ref(null);

type Element = {
    name: string;
    average: number;
};

// Elemental data averages
const averages: Element[] = [
    { name: "AlK", average: 5.011877188406048 },
    { name: "ArK", average: 6.008377314893258 },
    { name: "AsK", average: 13.876968531085513 },
    { name: "BaL", average: 5.453845565815511 },
    { name: "BrK", average: 5.468149259636079 },
    { name: "CaK", average: 5.788856200986206 },
    { name: "CoK", average: 9.669387652168842 },
    { name: "CrK", average: 9.965356689991276 },
    { name: "CuK", average: 13.325969754977331 },
    { name: "FeK", average: 6.991524174818721 },
    { name: "HgL", average: 5.9448366029554665 },
    { name: "KK", average: 5.337136881227328 },
    { name: "MnK", average: 5.324313994056284 },
    { name: "NiK", average: 5.245180285648312 },
    { name: "PK", average: 5.017180982313069 },
    { name: "PbL", average: 52.61567826697549 },
    { name: "PbM", average: 6.020635147052218 },
    { name: "RhK", average: 5.761447486529703 },
    { name: "RhL", average: 5.293345511831873 },
    { name: "SK", average: 5.195613061045643 },
    { name: "SeK", average: 5.173119615920208 },
    { name: "SiK", average: 5.011643916044016 },
    { name: "SrK", average: 5.160192701885014 },
    { name: "ZnK", average: 36.44537919762188 },
    { name: "chi", average: 5.000119000427929 },
    { name: "cont.", average: 32.59123116581803 }
];

function setup() {
    // Declare chart dimensions and margins
    const width = 400;
    const height = 400;
    const margin = {top: 10, right: 30, bottom: 30, left: 60};

    // Select SVG container
    const svg = d3.select(chart.value)
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;");

    // Declare the horizontal position scale
    const x = d3.scaleBand()
        .domain(averages.map(d => d.name))
        .range([0, width])
        .padding(0.2);
    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
            .attr("transform", "translate(-10,0)rotate(-45)")
            .style("text-anchor", "end");

    // Declare the vertical position scale
    const y = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0]);
    svg.append("g")
        .call(d3.axisLeft(y));

    // Add data
    svg.selectAll("svg")
      .data(averages)
      .join("rect")
        .attr("x", d => <number>x(d.name))
        .attr("y", d => y(d.average))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d.average))
        .attr("fill", "#69b3a2");
}

// TODO: change this to Window 'onOpen' callback
watch(chart, (n, o) => {
    console.log(n, o)
    if (chart != null) {
        setup();
    }
});
</script>

<template>
    <Window title="Bar Chart Window" opened>
        <svg ref="chart"></svg>
    </Window>
</template>
