var bt=Object.defineProperty;var At=Object.getOwnPropertyDescriptor;var S=(o,t,e,s)=>{for(var i=s>1?void 0:s?At(t,e):t,n=o.length-1,r;n>=0;n--)(r=o[n])&&(i=(s?r(t,e,i):r(i))||i);return s&&i&&bt(t,e,i),i};var L=globalThis,z=L.ShadowRoot&&(L.ShadyCSS===void 0||L.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,W=Symbol(),it=new WeakMap,M=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==W)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(z&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=it.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&it.set(e,t))}return t}toString(){return this.cssText}},ot=o=>new M(typeof o=="string"?o:o+"",void 0,W),_=(o,...t)=>{let e=o.length===1?o[0]:t.reduce((s,i,n)=>s+(r=>{if(r._$cssResult$===!0)return r.cssText;if(typeof r=="number")return r;throw Error("Value passed to 'css' function must be a 'css' function result: "+r+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+o[n+1],o[0]);return new M(e,o,W)},F=(o,t)=>{if(z)o.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=L.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,o.appendChild(s)}},D=z?o=>o:o=>o instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return ot(e)})(o):o;var{is:wt,defineProperty:xt,getOwnPropertyDescriptor:St,getOwnPropertyNames:Et,getOwnPropertySymbols:Ct,getPrototypeOf:Pt}=Object,I=globalThis,nt=I.trustedTypes,Mt=nt?nt.emptyScript:"",kt=I.reactiveElementPolyfillSupport,k=(o,t)=>o,R={toAttribute(o,t){switch(t){case Boolean:o=o?Mt:null;break;case Object:case Array:o=o==null?o:JSON.stringify(o)}return o},fromAttribute(o,t){let e=o;switch(t){case Boolean:e=o!==null;break;case Number:e=o===null?null:Number(o);break;case Object:case Array:try{e=JSON.parse(o)}catch{e=null}}return e}},q=(o,t)=>!wt(o,t),rt={attribute:!0,type:String,converter:R,reflect:!1,hasChanged:q};Symbol.metadata??=Symbol("metadata"),I.litPropertyMetadata??=new WeakMap;var m=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=rt){if(e.state&&(e.attribute=!1),this._$Ei(),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&xt(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:n}=St(this.prototype,t)??{get(){return this[e]},set(r){this[e]=r}};return{get(){return i?.call(this)},set(r){let c=i?.call(this);n.call(this,r),this.requestUpdate(t,c,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??rt}static _$Ei(){if(this.hasOwnProperty(k("elementProperties")))return;let t=Pt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(k("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(k("properties"))){let e=this.properties,s=[...Et(e),...Ct(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(D(i))}else t!==void 0&&e.push(D(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return F(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$EC(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let n=(s.converter?.toAttribute!==void 0?s.converter:R).toAttribute(e,s.type);this._$Em=t,n==null?this.removeAttribute(i):this.setAttribute(i,n),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let n=s.getPropertyOptions(i),r=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:R;this._$Em=i,this[i]=r.fromAttribute(e,n.type),this._$Em=null}}requestUpdate(t,e,s){if(t!==void 0){if(s??=this.constructor.getPropertyOptions(t),!(s.hasChanged??q)(this[t],e))return;this.P(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$ET())}P(t,e,s){this._$AL.has(t)||this._$AL.set(t,e),s.reflect===!0&&this._$Em!==t&&(this._$Ej??=new Set).add(t)}async _$ET(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,n]of this._$Ep)this[i]=n;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,n]of s)n.wrapped!==!0||this._$AL.has(i)||this[i]===void 0||this.P(i,this[i],n)}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EU()}catch(s){throw t=!1,this._$EU(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EU(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Ej&&=this._$Ej.forEach(e=>this._$EC(e,this[e])),this._$EU()}updated(t){}firstUpdated(t){}};m.elementStyles=[],m.shadowRootOptions={mode:"open"},m[k("elementProperties")]=new Map,m[k("finalized")]=new Map,kt?.({ReactiveElement:m}),(I.reactiveElementVersions??=[]).push("2.0.4");var G=globalThis,V=G.trustedTypes,at=V?V.createPolicy("lit-html",{createHTML:o=>o}):void 0,ut="$lit$",g=`lit$${Math.random().toFixed(9).slice(2)}$`,mt="?"+g,Rt=`<${mt}>`,A=document,O=()=>A.createComment(""),H=o=>o===null||typeof o!="object"&&typeof o!="function",tt=Array.isArray,Ut=o=>tt(o)||typeof o?.[Symbol.iterator]=="function",J=`[ 	
\f\r]`,U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,lt=/-->/g,ct=/>/g,v=RegExp(`>|${J}(?:([^\\s"'>=/]+)(${J}*=${J}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ht=/'/g,dt=/"/g,ft=/^(?:script|style|textarea|title)$/i,et=o=>(t,...e)=>({_$litType$:o,strings:t,values:e}),st=et(1),Bt=et(2),Wt=et(3),w=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),pt=new WeakMap,b=A.createTreeWalker(A,129);function gt(o,t){if(!tt(o)||!o.hasOwnProperty("raw"))throw Error("invalid template strings array");return at!==void 0?at.createHTML(t):t}var Ot=(o,t)=>{let e=o.length-1,s=[],i,n=t===2?"<svg>":t===3?"<math>":"",r=U;for(let c=0;c<e;c++){let a=o[c],d,p,l=-1,u=0;for(;u<a.length&&(r.lastIndex=u,p=r.exec(a),p!==null);)u=r.lastIndex,r===U?p[1]==="!--"?r=lt:p[1]!==void 0?r=ct:p[2]!==void 0?(ft.test(p[2])&&(i=RegExp("</"+p[2],"g")),r=v):p[3]!==void 0&&(r=v):r===v?p[0]===">"?(r=i??U,l=-1):p[1]===void 0?l=-2:(l=r.lastIndex-p[2].length,d=p[1],r=p[3]===void 0?v:p[3]==='"'?dt:ht):r===dt||r===ht?r=v:r===lt||r===ct?r=U:(r=v,i=void 0);let f=r===v&&o[c+1].startsWith("/>")?" ":"";n+=r===U?a+Rt:l>=0?(s.push(d),a.slice(0,l)+ut+a.slice(l)+g+f):a+g+(l===-2?c:f)}return[gt(o,n+(o[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},N=class o{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let n=0,r=0,c=t.length-1,a=this.parts,[d,p]=Ot(t,e);if(this.el=o.createElement(d,s),b.currentNode=this.el.content,e===2||e===3){let l=this.el.content.firstChild;l.replaceWith(...l.childNodes)}for(;(i=b.nextNode())!==null&&a.length<c;){if(i.nodeType===1){if(i.hasAttributes())for(let l of i.getAttributeNames())if(l.endsWith(ut)){let u=p[r++],f=i.getAttribute(l).split(g),j=/([.?@])?(.*)/.exec(u);a.push({type:1,index:n,name:j[2],strings:f,ctor:j[1]==="."?X:j[1]==="?"?Y:j[1]==="@"?Z:C}),i.removeAttribute(l)}else l.startsWith(g)&&(a.push({type:6,index:n}),i.removeAttribute(l));if(ft.test(i.tagName)){let l=i.textContent.split(g),u=l.length-1;if(u>0){i.textContent=V?V.emptyScript:"";for(let f=0;f<u;f++)i.append(l[f],O()),b.nextNode(),a.push({type:2,index:++n});i.append(l[u],O())}}}else if(i.nodeType===8)if(i.data===mt)a.push({type:2,index:n});else{let l=-1;for(;(l=i.data.indexOf(g,l+1))!==-1;)a.push({type:7,index:n}),l+=g.length-1}n++}}static createElement(t,e){let s=A.createElement("template");return s.innerHTML=t,s}};function E(o,t,e=o,s){if(t===w)return t;let i=s!==void 0?e.o?.[s]:e.l,n=H(t)?void 0:t._$litDirective$;return i?.constructor!==n&&(i?._$AO?.(!1),n===void 0?i=void 0:(i=new n(o),i._$AT(o,e,s)),s!==void 0?(e.o??=[])[s]=i:e.l=i),i!==void 0&&(t=E(o,i._$AS(o,t.values),i,s)),t}var K=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??A).importNode(e,!0);b.currentNode=i;let n=b.nextNode(),r=0,c=0,a=s[0];for(;a!==void 0;){if(r===a.index){let d;a.type===2?d=new T(n,n.nextSibling,this,t):a.type===1?d=new a.ctor(n,a.name,a.strings,this,t):a.type===6&&(d=new Q(n,this,t)),this._$AV.push(d),a=s[++c]}r!==a?.index&&(n=b.nextNode(),r++)}return b.currentNode=A,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},T=class o{get _$AU(){return this._$AM?._$AU??this.v}constructor(t,e,s,i){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this.v=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=E(this,t,e),H(t)?t===h||t==null||t===""?(this._$AH!==h&&this._$AR(),this._$AH=h):t!==this._$AH&&t!==w&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Ut(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==h&&H(this._$AH)?this._$AA.nextSibling.data=t:this.T(A.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=N.createElement(gt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let n=new K(i,this),r=n.u(this.options);n.p(e),this.T(r),this._$AH=n}}_$AC(t){let e=pt.get(t.strings);return e===void 0&&pt.set(t.strings,e=new N(t)),e}k(t){tt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let n of t)i===e.length?e.push(s=new o(this.O(O()),this.O(O()),this,this.options)):s=e[i],s._$AI(n),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t&&t!==this._$AB;){let s=t.nextSibling;t.remove(),t=s}}setConnected(t){this._$AM===void 0&&(this.v=t,this._$AP?.(t))}},C=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,n){this.type=1,this._$AH=h,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=n,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=h}_$AI(t,e=this,s,i){let n=this.strings,r=!1;if(n===void 0)t=E(this,t,e,0),r=!H(t)||t!==this._$AH&&t!==w,r&&(this._$AH=t);else{let c=t,a,d;for(t=n[0],a=0;a<n.length-1;a++)d=E(this,c[s+a],e,a),d===w&&(d=this._$AH[a]),r||=!H(d)||d!==this._$AH[a],d===h?t=h:t!==h&&(t+=(d??"")+n[a+1]),this._$AH[a]=d}r&&!i&&this.j(t)}j(t){t===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},X=class extends C{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===h?void 0:t}},Y=class extends C{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==h)}},Z=class extends C{constructor(t,e,s,i,n){super(t,e,s,i,n),this.type=5}_$AI(t,e=this){if((t=E(this,t,e,0)??h)===w)return;let s=this._$AH,i=t===h&&s!==h||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,n=t!==h&&(s===h||i);i&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},Q=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){E(this,t)}};var Ht=G.litHtmlPolyfillSupport;Ht?.(N,T),(G.litHtmlVersions??=[]).push("3.2.0");var yt=(o,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let n=e?.renderBefore??null;s._$litPart$=i=new T(t.insertBefore(O(),n),n,void 0,e??{})}return i._$AI(o),i};var y=class extends m{constructor(){super(...arguments),this.renderOptions={host:this},this.o=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this.o=yt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this.o?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this.o?.setConnected(!1)}render(){return w}};y._$litElement$=!0,y.finalized=!0,globalThis.litElementHydrateSupport?.({LitElement:y});var Nt=globalThis.litElementPolyfillSupport;Nt?.({LitElement:y});(globalThis.litElementVersions??=[]).push("4.1.0");var Tt={attribute:!0,type:String,converter:R,reflect:!1,hasChanged:q},jt=(o=Tt,t,e)=>{let{kind:s,metadata:i}=e,n=globalThis.litPropertyMetadata.get(i);if(n===void 0&&globalThis.litPropertyMetadata.set(i,n=new Map),n.set(e.name,o),s==="accessor"){let{name:r}=e;return{set(c){let a=t.get.call(this);t.set.call(this,c),this.requestUpdate(r,a,o)},init(c){return c!==void 0&&this.P(r,void 0,o),c}}}if(s==="setter"){let{name:r}=e;return function(c){let a=this[r];t.call(this,c),this.requestUpdate(r,a,o)}}throw Error("Unsupported decorator location: "+s)};function x(o){return(t,e)=>typeof e=="object"?jt(o,t,e):((s,i,n)=>{let r=i.hasOwnProperty(n);return i.constructor.createProperty(n,r?{...s,wrapped:!0}:s),r?Object.getOwnPropertyDescriptor(i,n):void 0})(o,t,e)}var $t=_`
    .legacy-button {
        align-items: center;
        background-color: var(--jp-layout-color2);
        border-width: 0;
        box-shadow: none;
        color: var(--jp-ui-font-color1);
        cursor: pointer;
        display: flex;
        font-family: "Helvetica Neue", Arial, Helvetica, sans-serif;
        font-size: var(--jp-widgets-font-size);
        justify-content: center;
        line-height: var(--jp-widgets-inline-height);
        padding: 0;
    }

    .legacy-button.primary {
        background-color: var(--jp-brand-color1);
        color: var(--jp-ui-inverse-font-color1);
    }

    .legacy-button:hover:enabled,
    .legacy-button:focus:enabled {
        box-shadow: 0 2px 2px 0 rgba(0, 0, 0, var(--md-shadow-key-penumbra-opacity)),
                    0 3px 1px -2px rgba(0, 0, 0, var(--md-shadow-key-umbra-opacity)),
                    0 1px 5px 0 rgba(0, 0, 0, var(--md-shadow-ambient-shadow-opacity));
    }

    .legacy-slider {
        -webkit-appearance: none;
        appearance: none;
        background: var(--jp-layout-color3);
        border-radius: 3px;
        height: 4px;
        outline: none;
    }

    .legacy-slider::-webkit-slider-thumb,
    .legacy-slider::-moz-range-thumb {
        -moz-appearance: none;
        -webkit-appearance: none;
        appearance: none;
        border-radius: 50%;
        cursor: pointer;
        height: var(--jp-widgets-slider-handle-size);
        width: var(--jp-widgets-slider-handle-size);
    }

    .legacy-text {
        color: var(--jp-widgets-label-color);
        font-family: "Helvetica Neue", Arial, Helvetica, sans-serif;
        font-size: var(--jp-widgets-font-size);
        height: var(--jp-widgets-inline-height);
        line-height: var(--jp-widgets-inline-height);
    }
`;var _t=_`
    @font-face {
        font-family: 'Material Symbols Outlined';
        font-style: normal;
        font-weight: 400;
        src: url(https://fonts.gstatic.com/s/materialsymbolsoutlined/v205/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1v-p_4MrImHCIJIZrDCvHOejbd5zrDAt.woff2) format('woff2');
    }

    .material-symbols-outlined {
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        direction: ltr;
        display: inline-block;
        font-family: 'Material Symbols Outlined';
        font-style: normal;
        font-weight: normal;
        letter-spacing: normal;
        line-height: 1;
        text-transform: none;
        white-space: nowrap;
        word-wrap: normal;
    }
`;function vt(){if(!document.querySelector(".custom-fonts")){let o=document.createElement("style");o.classList.add("custom-fonts"),o.textContent='@import "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined";',document.body.appendChild(o)}}var $=class $ extends y{constructor(){super(...arguments);this._model=void 0;this.name="";this.visible=!0;this.opacity=0;this.isLoading=!1;this.isConfirmDialogVisible=!1}static get componentName(){return"layer-manager-row"}static{this.styles=[$t,_t,_`
            .row {
                align-items: center;
                display: flex;
                gap: 4px;
                height: 30px;
            }

            .layer-name {
                flex-grow: 1;
                max-width: 150px;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .settings-delete-button {
                font-size: 14px;
                height: 26px;
                width: 26px;
            }

            .layer-opacity-slider {
                width: 70px;
            }

            .layer-visibility-checkbox {
                margin: 2px;
            }

            .spinner {
                -webkit-animation: spin 2s linear infinite;
                animation: spin 2s linear infinite;
                border-radius: 50%;
                border: 4px solid var(--jp-widgets-input-border-color);
                border-top: 4px solid var(--jp-widgets-color);
                height: 12px;
                width: 12px;
            }

            @-webkit-keyframes spin {
                0% { -webkit-transform: rotate(0deg); }
                100% { -webkit-transform: rotate(360deg); }
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            button.loading .spinner,
            button.loading:hover .close-icon,
            button.done-loading .close-icon {
                display: block;
            }

            button.loading .close-icon,
            button.loading:hover .spinner,
            button.done-loading .spinner {
                display: none;
            }

            .remove-layer-text {
                flex-grow: 1;
            }

            .confirm-deny-button {
                height: 26px;
                width: 70px;
            }
        `]}static{this.modelNameToViewName=new Map([["name","name"],["visible","visible"],["opacity","opacity"],["is_loading","isLoading"]])}set model(e){this._model=e;for(let[s,i]of $.modelNameToViewName)i&&(this[i]=e.get(s),e.on(`change:${s}`,()=>{this[i]=e.get(s)}))}render(){return st`
            <div class="row">
                <input
                    type="checkbox"
                    class="layer-visibility-checkbox"
                    .checked="${this.visible}"
                    @change="${this.onLayerVisibilityChanged}"
                />
                <span class="legacy-text layer-name">${this.name}</span>
                <input
                    type="range"
                    class="legacy-slider layer-opacity-slider"
                    min="0"
                    max="1"
                    step="0.01"
                    .value="${this.opacity}"
                    @input="${this.onLayerOpacityChanged}"
                />
                <button
                    class="legacy-button settings-delete-button"
                    @click="${this.onSettingsClicked}"
                >
                    <span class="material-symbols-outlined">&#xe8b8;</span>
                </button>
                <button
                    class="legacy-button settings-delete-button ${this.isLoading?"loading":"done-loading"}"
                    @click="${this.onDeleteClicked}"
                >
                    <div class="spinner"></div>
                    <span class="close-icon material-symbols-outlined">&#xe5cd;</span>
                </button>
            </div>
            ${this.renderConfirmDialog()}
        `}renderConfirmDialog(){return this.isConfirmDialogVisible?st`
            <div class="row">
                <span class="legacy-text remove-layer-text">Remove layer?</span>
                    <button
                        class="legacy-button primary confirm-deny-button"
                        @click="${this.confirmDeletion}"
                    >
                        Yes
                    </button>
                    <button
                        class="legacy-button primary confirm-deny-button"
                        @click="${this.cancelDeletion}"
                    >
                        No
                    </button>
            </div>
        `:h}updated(e){for(let[s,i]of e)this._model?.set(s,this[s]);this._model?.save_changes()}onLayerVisibilityChanged(e){let s=e.target;this.visible=s.checked}onLayerOpacityChanged(e){let s=e.target;this.opacity=parseFloat(s.value)}onSettingsClicked(e){this._model?.send({type:"click",id:"settings"})}onDeleteClicked(e){this.isConfirmDialogVisible=!0}confirmDeletion(e){this._model?.send({type:"click",id:"delete"})}cancelDeletion(e){this.isConfirmDialogVisible=!1}};S([x()],$.prototype,"name",2),S([x()],$.prototype,"visible",2),S([x()],$.prototype,"opacity",2),S([x()],$.prototype,"isLoading",2),S([x()],$.prototype,"isConfirmDialogVisible",2);var P=$;customElements.get(P.componentName)||customElements.define(P.componentName,P);function Lt({model:o,el:t}){vt();let e=document.createElement(P.componentName);e.model=o,t.appendChild(e)}var qe={render:Lt};export{P as LayerManagerRow,qe as default};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/custom-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/property.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/state.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/event-options.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/base.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-all.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-async.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
