package com.disaster.stormsurge.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    @Value("${fastapi.base-url:http://localhost:8000}")
    private String fastApiBaseUrl;

    @Value("${fastapi.connect-timeout-ms:3000}")
    private int connectTimeout;

    @Value("${fastapi.read-timeout-ms:5000}")
    private int readTimeout;

    @Bean
    public RestClient fastApiRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(connectTimeout);
        requestFactory.setReadTimeout(readTimeout);

        return RestClient.builder()
                .baseUrl(fastApiBaseUrl)
                .requestFactory(requestFactory)
                .build();
    }
}
