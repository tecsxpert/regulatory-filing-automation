package com.internship.tool.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.internship.tool.dto.FilingRequestDto;
import com.internship.tool.service.RegulatoryFilingService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class RegulatoryFilingControllerTest {

    @Autowired 
    private MockMvc mockMvc;
    
    @Autowired 
    private ObjectMapper objectMapper;
    
    @MockBean  
    private RegulatoryFilingService filingService;

    @Test
    @WithMockUser(roles = "VIEWER")
    void getAll_returns200() throws Exception {
        mockMvc.perform(get("/api/filings"))
               .andExpect(status().isOk());
    }

    @Test
    void getAll_withoutAuth_returns401() throws Exception {
        mockMvc.perform(get("/api/filings"))
               .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void delete_returns204() throws Exception {
        Mockito.doNothing().when(filingService).softDelete(1L);
        mockMvc.perform(delete("/api/filings/1"))
               .andExpect(status().isNoContent());
    }

    @Test
    @WithMockUser(roles = "VIEWER")
    void delete_asViewer_returns403() throws Exception {
        mockMvc.perform(delete("/api/filings/1"))
               .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "MANAGER")
    void update_withValidBody_returns200() throws Exception {
        FilingRequestDto req = new FilingRequestDto();
        req.setTitle("Updated Title");
        req.setStatus("SUBMITTED");

        mockMvc.perform(put("/api/filings/1")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
               .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "VIEWER")
    void search_returns200() throws Exception {
        mockMvc.perform(get("/api/filings/search?q=test"))
               .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "VIEWER")
    void stats_returns200() throws Exception {
        mockMvc.perform(get("/api/filings/stats"))
               .andExpect(status().isOk());
    }

    @Test
    void login_withValidCredentials_returns200() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"admin\",\"password\":\"Admin@123\"}"))
               .andExpect(status().isOk());
    }
}