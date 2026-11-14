#!/usr/bin/env node
"use strict";
// Dependency-free smoke test: execute app startup with a small mocked DOM/catalog.
// This catches runtime errors that node --check cannot detect.
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");

const mkEl=()=>({
  innerHTML:"",dataset:{},style:{},open:false,
  classList:{add(){},remove(){},toggle(){}},
  addEventListener(){},setAttribute(){},removeAttribute(){},
  focus(){},close(){this.open=false},showModal(){this.open=true}
});
const elements=new Map();
const querySelector=key=>{
  if(!elements.has(key))elements.set(key,mkEl());
  return elements.get(key);
};
const document={
  querySelector,
  querySelectorAll(){return []},
  addEventListener(){},
  body:{style:{}},
  title:""
};
const movie=(id,title,year,genre)=>({
  id,title,year,type:"Movie",genres:[genre],
  languages:["Hindi","Tamil"],poster:"photos/photo_1.jpg",thumbnail:"photos/photo_1.jpg",
  sources:[{host:"example.org",label:"1080p",url:"https://example.org/file"}],
  added:"2026-11-01",reactions:1,sourceIds:[id]
});
const movies=[
  movie(2027,"RRR",2022,"Action"),
  movie(1958,"Salaar",2023,"Thriller"),
  movie(3012,"Maharaja",2024,"Drama")
];
const errors=[];
const sandbox={
  document,
  window:{addEventListener(){},scrollTo(){}},
  fetch:async()=>({ok:true,json:async()=>({movies})}),
  localStorage:{getItem(){return null},setItem(){}},
  history:{replaceState(){},back(){}},
  location:{hash:"",href:"https://example.org/"},
  navigator:{},
  URL,URLSearchParams,Intl,
  setTimeout:()=>1,clearTimeout(){},scrollY:0,scrollTo(){},
  matchMedia:()=>({matches:false}),
  console:{error:(...args)=>errors.push(args.map(String).join(" ")),info(){}}
};
const app=fs.readFileSync("assets/app.js","utf8");
vm.runInNewContext(app,sandbox,{filename:"assets/app.js"});
setImmediate(()=>{
 const html=querySelector("#main").innerHTML;
 assert.equal(errors.length,0,"App errors: "+errors.join("; "));
 assert.match(html,/Featured movie/,"Hero did not render");
 assert.match(html,/movie-card/,"Movie cards did not render");
 assert.doesNotMatch(html,/The collection couldn.t load/,"Startup entered error state");
 console.log("PASS: Southscreen app initializes and renders homepage with mock catalog");
});
