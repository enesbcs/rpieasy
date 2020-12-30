function getDatas() {
 var taskstr = ""
 var i;
 for (i=0;i<elements.length;i++) {
  taskstr = taskstr + elements[i].toString()+",";
 }
 commandurl = ownurl+'/csv?header=0&tasks='+ taskstr;
 console.log(commandurl);
 fetch(commandurl, {mode: 'cors',credentials: 'same-origin',cache: 'no-cache',method:'GET',redirect: 'follow'})
  .then(response => response.text())
  .then(text => setDatas(text));
}

function setDatas(datas){
 values = datas.split(';');
 refreshDatas();
}

function refreshDatas() {
 var i;
 for (i=0;i<elements.length;i++) {
  setevalue("value_"+elements[i].toString());
 }
}

function setGaugeValue(gauge, value, minv,maxv) {
  valueold = value
  if ((minv != 0) && (maxv != 100)) {
   value = (value * (maxv - minv) / (maxv+minv)) + minv
  }
  if (value<0) {
   value = 0;
  }
  if (value>100){
   value = 100;
  }
  gauge.querySelector(".gauge__fill").style.transform = `rotate(${
    value / 200
  }turn)`;
  gauge.querySelector(".gauge__cover").textContent = `${Math.round(
    valueold
  )}`;
}

function setevalue(valname){
  var j,i;
  i=0;
  for (j=0;j<elements.length;j++) {
   if ('value_'+elements[j] == valname) {
    i=j;
    break
   }
  }
  aElement = document.getElementById(valname);
  if (aElement) {
   mtype = aElement.tagName.toLowerCase();
   console.log(values[i],valname);
   if ((mtype!="meter") && (mtype!="select")){
    mtype = aElement.getAttribute("class");
   }
    switch (mtype){
     case "textval":
      aElement.innerText = values[i];
     break
     case "state":
     case "cmn-toggle cmn-toggle-round":
      aElement.checked = Boolean(Number(values[i]));
     break
     case "meter":
     case "slider":
     case "select":
      aElement.value = Number(values[i]);
     break
     case "gauge":
      minv = Number(props[i][0])
      maxv = Number(props[i][1])
      setGaugeValue(aElement,Number(values[i]),minv,maxv);
     break
    }
  }  // aElement end
}

function cboxchanged(cboxelement){
  var tarr = cboxelement.id.split("_");
  var tasknum = tarr[1];
  var valnum = tarr[2];
  if (cboxelement.checked) {
    changestate(tasknum,valnum,"1");
  } else {
    changestate(tasknum,valnum,"0");
  }
}

function sselchanged(sselelement){
  var tarr = sselelement.id.split("_");
  var tasknum = tarr[1];
  var valnum = tarr[2];
  changestate(tasknum,valnum,sselelement.value);
}

function changestate(tasknum,valuenum,value){
  tn = Number(tasknum)+1
  vn = Number(valuenum)+1
  commandurl = ownurl+ '/control?cmd=taskvalueset,'+ tn.toString() + ','+ vn.toString() + ','+ value.toString();
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET",commandurl,true);
  xmlHttp.send(null);
}
