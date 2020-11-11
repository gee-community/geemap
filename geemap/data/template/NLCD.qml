<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" minScale="1e+08" version="3.16.0-Hannover" maxScale="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="0" mode="0" fetchMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling maxOversampling="2" enabled="false" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer nodataColor="" alphaBand="-1" band="1" opacity="1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry alpha="255" color="#466b9f" value="11" label="Open Water"/>
        <paletteEntry alpha="255" color="#d1def8" value="12" label="Perennial Ice/Snow"/>
        <paletteEntry alpha="255" color="#dec5c5" value="21" label="Developed, Open Space"/>
        <paletteEntry alpha="255" color="#d99282" value="22" label="Developed, Low Intensity"/>
        <paletteEntry alpha="255" color="#eb0000" value="23" label="Developed, Medium Intensity"/>
        <paletteEntry alpha="255" color="#ab0000" value="24" label="Developed High Intensity"/>
        <paletteEntry alpha="255" color="#b3ac9f" value="31" label="Barren Land (Rock/Sand/Clay)"/>
        <paletteEntry alpha="255" color="#68ab5f" value="41" label="Deciduous Forest"/>
        <paletteEntry alpha="255" color="#1c5f2c" value="42" label="Evergreen Forest"/>
        <paletteEntry alpha="255" color="#b5c58f" value="43" label="Mixed Forest"/>
        <paletteEntry alpha="255" color="#af963c" value="51" label="Dwarf Scrub"/>
        <paletteEntry alpha="255" color="#ccb879" value="52" label="Shrub/Scrub"/>
        <paletteEntry alpha="255" color="#dfdfc2" value="71" label="Grassland/Herbaceous"/>
        <paletteEntry alpha="255" color="#d1d182" value="72" label="Sedge/Herbaceous"/>
        <paletteEntry alpha="255" color="#a3cc51" value="73" label="Lichens"/>
        <paletteEntry alpha="255" color="#82ba9e" value="74" label="Moss"/>
        <paletteEntry alpha="255" color="#dcd939" value="81" label="Pasture/Hay"/>
        <paletteEntry alpha="255" color="#ab6c28" value="82" label="Cultivated Crops"/>
        <paletteEntry alpha="255" color="#b8d9eb" value="90" label="Woody Wetlands"/>
        <paletteEntry alpha="255" color="#6c9fb8" value="95" label="Emergent Herbaceous Wetlands"/>
      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeRed="255" colorizeBlue="128" saturation="0" grayscaleMode="0" colorizeStrength="100" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
