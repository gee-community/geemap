async function d(e,i){return Promise.all(e.map(t=>i.get_model(t.slice(10))))}async function l(e,i){let t=i.get("children"),a=await d(t,i.widget_manager),r=await Promise.all(a.map(n=>n.widget_manager.create_view(n)));e.innerHTML="";for(let n of r)e.appendChild(n.el)}export{l as updateChildren};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsiLi4vLi4vanMvdXRpbHMudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImltcG9ydCB0eXBlIHsgQW55TW9kZWwgfSBmcm9tIFwiQGFueXdpZGdldC90eXBlc1wiO1xuaW1wb3J0IHsgSVdpZGdldE1hbmFnZXIsIFdpZGdldE1vZGVsIH0gZnJvbSBcIkBqdXB5dGVyLXdpZGdldHMvYmFzZVwiO1xuXG5hc3luYyBmdW5jdGlvbiB1bnBhY2tNb2RlbHMobW9kZWxJZHM6IEFycmF5PHN0cmluZz4sIG1hbmFnZXI6IElXaWRnZXRNYW5hZ2VyKTogUHJvbWlzZTxBcnJheTxXaWRnZXRNb2RlbD4+IHtcbiAgICByZXR1cm4gUHJvbWlzZS5hbGwoXG4gICAgICAgIG1vZGVsSWRzLm1hcChpZCA9PiBtYW5hZ2VyLmdldF9tb2RlbChpZC5zbGljZShcIklQWV9NT0RFTF9cIi5sZW5ndGgpKSlcbiAgICApO1xufVxuXG5leHBvcnQgYXN5bmMgZnVuY3Rpb24gdXBkYXRlQ2hpbGRyZW4oY29udGFpbmVyOiBIVE1MRWxlbWVudCwgbW9kZWw6IEFueU1vZGVsPGFueT4pIHtcbiAgICBjb25zdCBjaGlsZHJlbiA9IG1vZGVsLmdldChcImNoaWxkcmVuXCIpO1xuICAgIGNvbnN0IGNoaWxkX21vZGVscyA9IGF3YWl0IHVucGFja01vZGVscyhjaGlsZHJlbiwgbW9kZWwud2lkZ2V0X21hbmFnZXIpO1xuICAgIGNvbnN0IGNoaWxkX3ZpZXdzID0gYXdhaXQgUHJvbWlzZS5hbGwoXG4gICAgICAgIGNoaWxkX21vZGVscy5tYXAobW9kZWwgPT4gbW9kZWwud2lkZ2V0X21hbmFnZXIuY3JlYXRlX3ZpZXcobW9kZWwpKVxuICAgICk7XG4gICAgY29udGFpbmVyLmlubmVySFRNTCA9IGBgO1xuICAgIGZvciAoY29uc3QgY2hpbGRfdmlldyBvZiBjaGlsZF92aWV3cykge1xuICAgICAgICBjb250YWluZXIuYXBwZW5kQ2hpbGQoY2hpbGRfdmlldy5lbCk7XG4gICAgfVxufVxuIl0sCiAgIm1hcHBpbmdzIjogIkFBR0EsZUFBZUEsRUFBYUMsRUFBeUJDLEVBQXNELENBQ3ZHLE9BQU8sUUFBUSxJQUNYRCxFQUFTLElBQUlFLEdBQU1ELEVBQVEsVUFBVUMsRUFBRyxNQUFNLEVBQW1CLENBQUMsQ0FBQyxDQUN2RSxDQUNKLENBRUEsZUFBc0JDLEVBQWVDLEVBQXdCQyxFQUFzQixDQUMvRSxJQUFNQyxFQUFXRCxFQUFNLElBQUksVUFBVSxFQUMvQkUsRUFBZSxNQUFNUixFQUFhTyxFQUFVRCxFQUFNLGNBQWMsRUFDaEVHLEVBQWMsTUFBTSxRQUFRLElBQzlCRCxFQUFhLElBQUlGLEdBQVNBLEVBQU0sZUFBZSxZQUFZQSxDQUFLLENBQUMsQ0FDckUsRUFDQUQsRUFBVSxVQUFZLEdBQ3RCLFFBQVdLLEtBQWNELEVBQ3JCSixFQUFVLFlBQVlLLEVBQVcsRUFBRSxDQUUzQyIsCiAgIm5hbWVzIjogWyJ1bnBhY2tNb2RlbHMiLCAibW9kZWxJZHMiLCAibWFuYWdlciIsICJpZCIsICJ1cGRhdGVDaGlsZHJlbiIsICJjb250YWluZXIiLCAibW9kZWwiLCAiY2hpbGRyZW4iLCAiY2hpbGRfbW9kZWxzIiwgImNoaWxkX3ZpZXdzIiwgImNoaWxkX3ZpZXciXQp9Cg==