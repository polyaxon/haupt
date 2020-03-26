// Copyright 2018-2020 Polyaxon, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/*
 * Polyaxon SDKs and REST API specification.
 * Polyaxon SDKs and REST API specification.
 *
 * OpenAPI spec version: 1.0.71
 * Contact: contact@polyaxon.com
 *
 * NOTE: This class is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 */


package io.swagger.client.model;

import java.util.Objects;
import java.util.Arrays;
import com.google.gson.TypeAdapter;
import com.google.gson.annotations.JsonAdapter;
import com.google.gson.annotations.SerializedName;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.io.IOException;

/**
 * Early stopping with diff factor stopping, this policy computes checks runs against the best run and stops those whose performance is worse than the best by the factor defined by the user.
 */
@ApiModel(description = "Early stopping with diff factor stopping, this policy computes checks runs against the best run and stops those whose performance is worse than the best by the factor defined by the user.")

public class V1DiffStoppingPolicy {
  @SerializedName("kind")
  private String kind = null;

  @SerializedName("percent")
  private Float percent = null;

  @SerializedName("evaluation_interval")
  private Integer evaluationInterval = null;

  @SerializedName("min_interval")
  private Integer minInterval = null;

  @SerializedName("min_samples")
  private Integer minSamples = null;

  public V1DiffStoppingPolicy kind(String kind) {
    this.kind = kind;
    return this;
  }

   /**
   * Get kind
   * @return kind
  **/
  @ApiModelProperty(value = "")
  public String getKind() {
    return kind;
  }

  public void setKind(String kind) {
    this.kind = kind;
  }

  public V1DiffStoppingPolicy percent(Float percent) {
    this.percent = percent;
    return this;
  }

   /**
   * Get percent
   * @return percent
  **/
  @ApiModelProperty(value = "")
  public Float getPercent() {
    return percent;
  }

  public void setPercent(Float percent) {
    this.percent = percent;
  }

  public V1DiffStoppingPolicy evaluationInterval(Integer evaluationInterval) {
    this.evaluationInterval = evaluationInterval;
    return this;
  }

   /**
   * Interval/Frequency for applying the policy.
   * @return evaluationInterval
  **/
  @ApiModelProperty(value = "Interval/Frequency for applying the policy.")
  public Integer getEvaluationInterval() {
    return evaluationInterval;
  }

  public void setEvaluationInterval(Integer evaluationInterval) {
    this.evaluationInterval = evaluationInterval;
  }

  public V1DiffStoppingPolicy minInterval(Integer minInterval) {
    this.minInterval = minInterval;
    return this;
  }

   /**
   * Get minInterval
   * @return minInterval
  **/
  @ApiModelProperty(value = "")
  public Integer getMinInterval() {
    return minInterval;
  }

  public void setMinInterval(Integer minInterval) {
    this.minInterval = minInterval;
  }

  public V1DiffStoppingPolicy minSamples(Integer minSamples) {
    this.minSamples = minSamples;
    return this;
  }

   /**
   * Get minSamples
   * @return minSamples
  **/
  @ApiModelProperty(value = "")
  public Integer getMinSamples() {
    return minSamples;
  }

  public void setMinSamples(Integer minSamples) {
    this.minSamples = minSamples;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    V1DiffStoppingPolicy v1DiffStoppingPolicy = (V1DiffStoppingPolicy) o;
    return Objects.equals(this.kind, v1DiffStoppingPolicy.kind) &&
        Objects.equals(this.percent, v1DiffStoppingPolicy.percent) &&
        Objects.equals(this.evaluationInterval, v1DiffStoppingPolicy.evaluationInterval) &&
        Objects.equals(this.minInterval, v1DiffStoppingPolicy.minInterval) &&
        Objects.equals(this.minSamples, v1DiffStoppingPolicy.minSamples);
  }

  @Override
  public int hashCode() {
    return Objects.hash(kind, percent, evaluationInterval, minInterval, minSamples);
  }


  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class V1DiffStoppingPolicy {\n");
    
    sb.append("    kind: ").append(toIndentedString(kind)).append("\n");
    sb.append("    percent: ").append(toIndentedString(percent)).append("\n");
    sb.append("    evaluationInterval: ").append(toIndentedString(evaluationInterval)).append("\n");
    sb.append("    minInterval: ").append(toIndentedString(minInterval)).append("\n");
    sb.append("    minSamples: ").append(toIndentedString(minSamples)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(java.lang.Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }

}

