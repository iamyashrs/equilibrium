
//-------------------------------------------------------------------------------------
//          Suggestions Dropdown/AutoCompleter
//          By: Erobo Software
//          http://www.erobo.net 
//          Copyright (c) 2010-2011 Erobo Software
//          
//     ********************************************************************************     
//     *     Released under the GNU General Public License                            *
//     *     This program is free software: you can redistribute it and/or modify     *
//     *     it under the terms of the GNU General Public License as published by     *
//     *     the Free Software Foundation, either version 3 of the License, or        *
//     *     (at your option) any later version.                                      *
//     *                                                                              *
//     *     This program is distributed in the hope that it will be useful,          *
//     *     but WITHOUT ANY WARRANTY; without even the implied warranty of           *
//     *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            *
//     *     GNU General Public License for more details.                             *
//     *                                                                              *
//     *     You should have received a copy of the GNU General Public License        *
//     *     along with this program.  If not, see <http://www.gnu.org/licenses/>.    *
//     ********************************************************************************
//
//-------------------------------------------------------------------------------------


var frameSu = "";
var SrcSuggestions = "";
var iframeLoaded = false;
var searchSuggestionsInProgress = false;
var previousSuggestionSuffix = "";
var capitalizeSuggestions = false;
var searchWholePhrases = false;

function initAutoCompleter(iniLeft, marginOffset, widthConf) {
  var ulLoc = document.getElementById("dropdown_q_suggestions");
  ulLoc.style.left = iniLeft + "px";
  var thisDrop = document.getElementById("ul_suggestions");
  thisDrop.style.marginLeft = marginOffset + "px";
  document.getElementById("ul_level_suggestions").style.width = (parseInt(widthConf) + 2) + "px";
  document.getElementById("container_sug").style.width = (parseInt(widthConf) + 2) + "px";
  document.getElementById("ul_suggestions").style.width = (parseInt(widthConf) + 2) + "px";
}

function hideAutoCompleter() {
  var ulMain = document.getElementById("ul_suggestions");
  ulMain.style.display = "";
}

function loadProcess(cylName) {

  var loadSuggestions = false;
  if (frameSu.src == "" || frameSu.src == "about:blank" || frameSu.src == null || frameSu.src.indexOf("_suggestions.htm") == -1) {
    loadSuggestions = true;
  }

  if (loadSuggestions == true) {
    this.frameSu.src = cylName; 
  }

  if (iframeLoaded == false) {
    if (frameSu.contentWindow.document.body == null) {
      setTimeout((function () { loadSuggestionsProc(cylName); }), 100);
      return false;
    }
  }

  if (iframeLoaded == false) {
    if (this.frameSu.contentWindow.document.body.innerHTML.indexOf("\|\-\*\-\|") == -1) {
      setTimeout((function () { loadSuggestionsProc(cylName); }), 100); //iframe has not been loaded yet
      return false;
    }
  }

  var frameSuRef = frameSu.contentWindow;
  var frameSuCnt = frameSuRef.document.getElementsByTagName('input');
  if (iframeLoaded == false) {
    for (var i = 0; i < frameSuCnt.length; i++) {
      SrcSuggestions = SrcSuggestions + frameSuRef.document.getElementById("cylinder" + i).innerHTML;
    }
  }

  iframeLoaded = true;

  try {

    document.getElementById("panel_q_suggestions").innerHTML = "";
    findPopulateSuggestions();
    document.getElementById("searchBox1").onkeyup = findPopulateSuggestions;

  } catch (e) {
    alert("There was an error Try Again..." + e.message)
  }
}

function loadSuggestionsProc(thisIframe) {

  if (SrcSuggestions == "") {
    loadProcess(thisIframe);
    return;
  } else {
    loadProcess(thisIframe);
  }
}

function findPopulateSuggestions() {

  var thisVal = document.getElementById("searchBox1").value;
  var idx1 = thisVal.lastIndexOf(" ");
  var splitIdx = (idx1 < 0 || searchWholePhrases)? 0 : idx1 + 1;
  var thisSuffix = thisVal.substring(splitIdx, thisVal.length)

  if(searchSuggestionsInProgress == false && thisSuffix.length > 1 && previousSuggestionSuffix != thisSuffix){
    searchSuggestionsInProgress = true;

    var targetWord = thisSuffix;
    var upperCaseWords = "N";
    var thisWord = "";
    var compositeWord = "";
    var wordIdx = 0;
    var numMatches = 0;
    var suggWordsArr = Array();
    var suggWordsArrIdx = 0;
    var suggMatchNumArr = Array();
    var suggMatchArrIdx = "";
    var highestIdx = 0;
    var seekCount = 0;
    var testCount = 0;
    var patt0=new RegExp(/[A-Z]/);
    
    if(patt0.test(targetWord.charAt(0))) {
      upperCaseWords = "Y";
    }
    
    targetWord = targetWord.toLowerCase();
    
    for(var i = 0; i < targetWord.length;i++) {
      compositeWord  = compositeWord + targetWord.charAt(i);
      if(compositeWord.length > 1) {

        wordIdx = SrcSuggestions.indexOf(("'" + compositeWord ));

        if(wordIdx > -1) {
          var wR = 0;
          seekCount = 0;
          while( wR <= targetWord.length + 1) {

            var startIdxW = 0;
            var currPointerW = 0;
            var retWordW = "";

            startIdxW = wordIdx + 1;
            currPointerW = startIdxW + 1;
            while(SrcSuggestions.substring(startIdxW ,currPointerW) != "'") {
              retWordW = retWordW + SrcSuggestions.substring(startIdxW,currPointerW);
              currPointerW = currPointerW + 1;
              startIdxW = startIdxW + 1;
            }

            thisWord = retWordW;
            wR = thisWord.length;
            suggWordsArr[suggWordsArrIdx] = thisWord;

            var thisWordM = thisWord;
            var targetWordM = targetWord;
            var numMatchesM = 0;
            var highestIdxM = -1;
            var sequenceStrM = "";
            for(var iM =0; iM < thisWordM.length; iM++) {

              if(iM < targetWordM.length) {
                for(var jM = highestIdxM + 1; jM < targetWordM.length;jM++) {

                  if(thisWordM.charAt(iM) == targetWordM.charAt(jM)) {
                    sequenceStrM = sequenceStrM + thisWordM.charAt(iM);
                    highestIdxM = jM;
                    break;
                  }   
                }
              }
            }
            
            numMatches = sequenceStrM.length;

            suggMatchArrIdx = ""+numMatches+"";
            if(suggMatchNumArr[suggMatchArrIdx] == null) {
              suggMatchNumArr[suggMatchArrIdx] = suggWordsArrIdx + "";
            } else {
              suggMatchNumArr[suggMatchArrIdx] = suggMatchNumArr[suggMatchArrIdx] + "," + suggWordsArrIdx;
            }

            if(numMatches > highestIdx) {
              highestIdx = numMatches;
            }
            
            suggWordsArrIdx = suggWordsArrIdx + 1;
            wordIdx = SrcSuggestions.indexOf(("'" + compositeWord),wordIdx + wR);
            if(wordIdx == -1) {
              break;
            } 
            if(seekCount > 3000) {
              break;
            }
            seekCount = seekCount + 1; 
          }
        }
      }
    }
    compositeWord = "";
    seekCount = 0;
    suggWordsArrIdx = suggWordsArrIdx + 1;

    var theseIndexes = Array();
    var resArray = Array();
    var resArrayIdx = 0;
    var currIdx = "";
    for(var k = highestIdx; k > -1; k--) {
      currIdx = "" + k + "";
      if(suggMatchNumArr[currIdx] != null) {
        theseIndexes = suggMatchNumArr[currIdx].split(",");
        for(var i = 0; i < theseIndexes.length; i++) {

          var iC = 0;
          var isInArr = false;
          for (iC=0; iC < resArray.length; iC++) {
            if (resArray[iC] == suggWordsArr[parseInt(theseIndexes[i])]) {
              isInArr = true;
            }
          }

          if(!isInArr) {
            if(resArray.length < 16) {
              if(upperCaseWords == "Y") {
                resArray[resArrayIdx] = suggWordsArr[theseIndexes[i]].substr(0, 1).toUpperCase();
                resArray[resArrayIdx] = resArray[resArrayIdx] + suggWordsArr[theseIndexes[i]].substr(1);
              } else {
                resArray[resArrayIdx] = suggWordsArr[theseIndexes[i]];
              }
              resArrayIdx = resArrayIdx + 1;
            } else {
              break;
            }
          }
        }
      }
    }

    var tbl = document.getElementById('suggestionsTbl');

    for(var jR = tbl.rows.length - 1; jR > -1; jR--) {
      tbl.deleteRow(jR);
    }

    var lastRow = 0;
    var row = null;
    var a = resArray;
    var temp = new Array();
    var suggContains = false;
    
    for(iH=0;iH<a.length;iH++){
      suggContains = false;
      for(jH=0;jH<temp.length;jH++){
        if(temp[jH]==a[iH]){
          suggContains = true
        }
      }
      
      if(suggContains == false){
        temp.length+=1;
        temp[temp.length-1]=a[iH];
      }
    }
    
    resArray = temp;
    
    for(var iR = 0; iR < resArray.length; iR++) {

      lastRow = tbl.rows.length;
      row = tbl.insertRow(lastRow);
      var cellLeft = row.insertCell(0);
      
      if(capitalizeSuggestions == true){
        var suggOld = resArray[iR];
        var suggNew = "";
        suggOld = suggOld.split(" ");
        for(var c=0; c < suggOld.length; c++) {
          if(suggNew == ""){
            suggNew += suggOld[c].substring(0,1).toUpperCase() + suggOld[c].substring(1,suggOld[c].length);
          }else{
            suggNew += ' ' + suggOld[c].substring(0,1).toUpperCase() + suggOld[c].substring(1,suggOld[c].length);
          }
        }
        cellLeft.innerHTML = suggNew;
      }else{
        cellLeft.innerHTML = resArray[iR];
      }
      cellLeft.setAttribute("width","100%");
      cellLeft.setAttribute("id",iR + "-" + 0);
      cellLeft.className = "defCell"
      
      cellLeft.onmouseover = function() {
        highLightSuggCell(this,true);
      };
      cellLeft.onmouseout = function() {
        highLightSuggCell(this,false);
      };
      cellLeft.onclick =  function() {
        selectSuggCell(this);
      }
    }

    document.getElementById("ul_suggestions").style.display = "block";
    previousSuggestionSuffix = thisSuffix;
    searchSuggestionsInProgress = false;
  }
}

function highLightSuggCell(thisObj,doHover) {   
  var thisCell = document.getElementById(thisObj.id);
  if(doHover == true && thisCell.className != "selCell") {
    thisCell.className = "suggCell";
  } else if(thisCell.className != "selCell") {
    thisCell.className = "defCell";
  }
}

function selectSuggCell(thisObj) {
  var thisCell = document.getElementById(thisObj.id);
  if(thisCell.className != "selCell") {
    deselectAllSugg(thisObj.id);
    thisCell.className = "selCell";
  } else {
    thisCell.className = "defCell";
  }

  var thisVal = document.getElementById("searchBox1").value;
  var idx1 = thisVal.lastIndexOf(" ");
  var splitIdx = (idx1 < 0 || searchWholePhrases) ? 0 : idx1 + 1;
  var thisSuffix = thisVal.substring(0, splitIdx);
  var thiseSearchBox = document.getElementById("searchBox1");
  thiseSearchBox.value = thisSuffix + thisCell.innerHTML;

  if (document.selection) { 
    thiseSearchBox.focus();
    var dropDownSelect = document.selection.createRange();
    dropDownSelect.moveStart ('character', thiseSearchBox.value.length);
    dropDownSelect.select();
  }else if (thiseSearchBox.selectionStart || thiseSearchBox.selectionStart == '0') {
    thiseSearchBox.selectionStart = thiseSearchBox.value.length;
    thiseSearchBox.selectionEnd = thiseSearchBox.value.length;
    thiseSearchBox.focus();
  }

  hideAutoCompleter();
}

function deselectAllSugg(thisId) {
  var tbl = document.getElementById('suggestionsTbl');
  var elemArr = tbl.getElementsByTagName("td");
  for(var i=0; i < elemArr.length;i++) {
    if(elemArr[i].id != thisId) {
      elemArr[i].className = "defCell";
    }
  }
}

function startSuggestionsDropDown(thisImage, thisImageClose, thisIframe, capitalizeSuggestionWords, searchForPhrases) {
  frameSu = document.getElementById("suggestions_iframe");
  var load_icon_ref = document.getElementById("suggestions_load_image");
  load_icon_ref.src = thisImage;
  load_icon_ref.style.display = "block";
  var suggestionsClose = document.getElementById("trigger_sug");
  suggestionsClose.style.backgroundImage = 'url(' + thisImageClose + ')';
  capitalizeSuggestions = capitalizeSuggestionWords;
  searchWholePhrases = searchForPhrases;
  loadSuggestionsProc(thisIframe);
}
